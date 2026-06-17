"""
views.py — Inventory Module
Future University LIMS
API endpoints for stock management and alerts
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q

from .models import StockItem, StockMovement, StockAlert
from .serializers import (
    StockItemSerializer, StockMovementSerializer,
    StockAlertSerializer, StockSummarySerializer,
)


class IsAdminOrTechnician(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.groups.filter(
            name__in=['Admin', 'Lab Technician']
        ).exists() or request.user.is_staff


class StockItemViewSet(viewsets.ModelViewSet):
    """
    Stock items — read for all authenticated, write for admin/technician.
    """
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['catalogue_item__common_name',
                          'catalogue_item__cas_number',
                          'lab_room__room_code', 'batch_number']
    ordering_fields    = ['quantity', 'last_updated']
    ordering           = ['lab_room__floor', 'catalogue_item__common_name']

    def get_queryset(self):
        qs     = StockItem.objects.select_related(
            'catalogue_item', 'lab_room'
        )
        params = self.request.query_params
        if params.get('room'):
            qs = qs.filter(lab_room_id=params['room'])
        if params.get('floor'):
            qs = qs.filter(lab_room__floor=params['floor'])
        if params.get('category'):
            qs = qs.filter(catalogue_item__category=params['category'])
        all_items = list(qs)
        if params.get('low_stock') == 'true':
            ids = [i.pk for i in all_items if i.is_low_stock]
            return StockItem.objects.filter(pk__in=ids).select_related(
                'catalogue_item', 'lab_room'
            )
        if params.get('expiring') == 'true':
            ids = [i.pk for i in all_items if i.is_expiring_soon]
            return StockItem.objects.filter(pk__in=ids).select_related(
                'catalogue_item', 'lab_room'
            )
        return qs

    def get_serializer_class(self):
        return StockItemSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrTechnician()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """Inventory dashboard summary."""
        all_items = StockItem.objects.select_related(
            'catalogue_item', 'lab_room'
        )
        low_stock    = [i for i in all_items if i.is_low_stock]
        out_of_stock = [i for i in all_items if i.is_out_of_stock]
        expiring     = [i for i in all_items if i.is_expiring_soon]
        expired      = [i for i in all_items if i.is_expired]
        alerts       = StockAlert.objects.filter(is_resolved=False).count()

        return Response({
            'total_items':          all_items.count(),
            'low_stock_count':      len(low_stock),
            'out_of_stock_count':   len(out_of_stock),
            'expiring_soon_count':  len(expiring),
            'expired_count':        len(expired),
            'unresolved_alerts':    alerts,
            'low_stock_items': StockItemSerializer(
                low_stock[:5], many=True
            ).data,
            'expiring_items': StockItemSerializer(
                expiring[:5], many=True
            ).data,
        })

    @action(detail=False, methods=['get'], url_path='by-room')
    def by_room(self, request):
        """Returns stock grouped by lab room."""
        from apps.booking.models import LabRoom
        rooms  = LabRoom.objects.all()
        result = {}
        for room in rooms:
            items = StockItem.objects.filter(
                lab_room=room
            ).select_related('catalogue_item')
            if items.exists():
                result[room.room_code] = {
                    'room_name':  room.name,
                    'floor':      room.get_floor_display(),
                    'item_count': items.count(),
                    'items': StockItemSerializer(items, many=True).data,
                }
        return Response(result)

    @action(detail=True, methods=['post'], url_path='set-minimum')
    def set_minimum(self, request, pk=None):
        """Set minimum stock threshold for alerts."""
        if not (request.user.is_staff or
                request.user.groups.filter(
                    name__in=['Admin', 'Lab Technician']
                ).exists()):
            return Response(status=status.HTTP_403_FORBIDDEN)

        stock_item = self.get_object()
        min_stock  = request.data.get('min_stock')
        if min_stock is None:
            return Response(
                {"detail": "min_stock value required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            stock_item.min_stock = float(min_stock)
            stock_item.save()
        except ValueError:
            return Response(
                {"detail": "Invalid min_stock value."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(StockItemSerializer(stock_item).data)

    @action(detail=False, methods=['post'], url_path='check-alerts')
    def check_alerts(self, request):
        """
        Scans all stock items and generates alerts for
        low stock, out of stock, expiring, and expired items.
        POST /api/stock/check-alerts/
        """
        if not (request.user.is_staff or
                request.user.groups.filter(
                    name__in=['Admin', 'Lab Technician']
                ).exists()):
            return Response(status=status.HTTP_403_FORBIDDEN)

        created = 0
        items   = StockItem.objects.select_related(
            'catalogue_item', 'lab_room'
        )

        for item in items:
            name = item.catalogue_item.common_name
            room = item.lab_room.room_code

            if item.is_expired:
                _, new = StockAlert.objects.get_or_create(
                    stock_item  = item,
                    alert_type  = 'expired',
                    is_resolved = False,
                    defaults    = {
                        'message': f"{name} in {room} expired on {item.expiry_date}."
                    }
                )
                if new: created += 1

            elif item.is_expiring_soon:
                days = (item.expiry_date - timezone.now().date()).days
                _, new = StockAlert.objects.get_or_create(
                    stock_item  = item,
                    alert_type  = 'expiring_soon',
                    is_resolved = False,
                    defaults    = {
                        'message': f"{name} in {room} expires in {days} days."
                    }
                )
                if new: created += 1

            if item.is_out_of_stock:
                _, new = StockAlert.objects.get_or_create(
                    stock_item  = item,
                    alert_type  = 'out_of_stock',
                    is_resolved = False,
                    defaults    = {
                        'message': f"{name} in {room} is out of stock."
                    }
                )
                if new: created += 1

            elif item.is_low_stock:
                _, new = StockAlert.objects.get_or_create(
                    stock_item  = item,
                    alert_type  = 'low_stock',
                    is_resolved = False,
                    defaults    = {
                        'message': (
                            f"{name} in {room} is low: "
                            f"{item.quantity} {item.unit} remaining "
                            f"(minimum: {item.min_stock})."
                        )
                    }
                )
                if new: created += 1

        return Response({
            "detail":  f"Alert check complete.",
            "created": created,
            "total_unresolved": StockAlert.objects.filter(
                is_resolved=False
            ).count(),
        })


class StockMovementViewSet(viewsets.ModelViewSet):
    """
    Stock movements — full audit trail.
    """
    permission_classes = [IsAdminOrTechnician]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['reference', 'notes',
                          'stock_item__catalogue_item__common_name']
    ordering           = ['-created_at']

    def get_queryset(self):
        qs     = StockMovement.objects.select_related(
            'stock_item__catalogue_item',
            'stock_item__lab_room',
            'performed_by',
        )
        params = self.request.query_params
        if params.get('stock_item'):
            qs = qs.filter(stock_item_id=params['stock_item'])
        if params.get('movement_type'):
            qs = qs.filter(movement_type=params['movement_type'])
        if params.get('room'):
            qs = qs.filter(stock_item__lab_room_id=params['room'])
        return qs

    def get_serializer_class(self):
        return StockMovementSerializer

    def get_permissions(self):
        return [IsAdminOrTechnician()]


class StockAlertViewSet(viewsets.ModelViewSet):
    """
    Stock alerts — admin/technician only.
    """
    permission_classes = [IsAdminOrTechnician]
    ordering           = ['-created_at']

    def get_queryset(self):
        qs     = StockAlert.objects.select_related(
            'stock_item__catalogue_item',
            'stock_item__lab_room',
            'resolved_by',
        )
        params = self.request.query_params
        if params.get('resolved') == 'false':
            qs = qs.filter(is_resolved=False)
        if params.get('alert_type'):
            qs = qs.filter(alert_type=params['alert_type'])
        return qs

    def get_serializer_class(self):
        return StockAlertSerializer

    @action(detail=True, methods=['post'], url_path='resolve')
    def resolve(self, request, pk=None):
        """Mark an alert as resolved."""
        alert = self.get_object()
        if alert.is_resolved:
            return Response(
                {"detail": "Alert already resolved."},
                status=status.HTTP_400_BAD_REQUEST
            )
        alert.is_resolved = True
        alert.resolved_by = request.user
        alert.resolved_at = timezone.now()
        alert.save()
        return Response(StockAlertSerializer(alert).data)

    @action(detail=False, methods=['post'], url_path='resolve-all')
    def resolve_all(self, request):
        """Resolve all unresolved alerts."""
        now     = timezone.now()
        updated = StockAlert.objects.filter(is_resolved=False).update(
            is_resolved = True,
            resolved_by = request.user,
            resolved_at = now,
        )
        return Response({
            "detail":  f"Resolved {updated} alerts.",
            "resolved": updated,
        })
