"""
views.py — Procurement Module
Future University LIMS
API endpoints for Purchase Orders and Goods Receipt
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction

from .models import PurchaseOrder, POLineItem, GoodsReceipt, GoodsReceiptItem
from .serializers import (
    PurchaseOrderSerializer, PurchaseOrderBriefSerializer,
    POLineItemSerializer,
    GoodsReceiptSerializer, GoodsReceiptItemSerializer,
)
from apps.needs.models import ConsolidatedRequest


class IsAdminOrTechnician(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.groups.filter(
            name__in=['Admin', 'Lab Technician']
        ).exists() or request.user.is_staff


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """
    Purchase Orders — admin/technician only.
    """
    permission_classes = [IsAdminOrTechnician]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['po_number', 'title', 'supplier']
    ordering_fields    = ['created_at', 'status', 'total_amount']
    ordering           = ['-created_at']

    def get_queryset(self):
        qs     = PurchaseOrder.objects.prefetch_related('line_items__catalogue_item')
        params = self.request.query_params
        if params.get('status'):
            qs = qs.filter(status=params['status'])
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return PurchaseOrderBriefSerializer
        return PurchaseOrderSerializer

    @action(detail=False, methods=['post'], url_path='generate-from-needs')
    def generate_from_needs(self, request):
        """
        Auto-generates a PO from all approved ConsolidatedRequests
        that don't have a PO yet.
        POST /api/purchase-orders/generate-from-needs/
        """
        approved = ConsolidatedRequest.objects.filter(
            status='approved'
        ).exclude(
            po_lines__isnull=False
        )

        if not approved.exists():
            return Response(
                {"detail": "No approved requests without a PO found."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            po = PurchaseOrder.objects.create(
                title    = f"Auto-generated PO — {timezone.now().strftime('%d %b %Y')}",
                status   = 'draft',
                created_by = request.user,
            )

            for cr in approved:
                POLineItem.objects.create(
                    purchase_order       = po,
                    catalogue_item       = cr.catalogue_item,
                    consolidated_request = cr,
                    quantity_ordered     = cr.approved_quantity or cr.total_quantity,
                    unit                 = cr.unit,
                )
                cr.status = 'ordered'
                cr.save()

            po.recalculate_total()

        return Response(
            PurchaseOrderSerializer(po, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='add-line')
    def add_line(self, request, pk=None):
        """
        Add a line item to an existing PO.
        POST /api/purchase-orders/{id}/add-line/
        """
        po = self.get_object()
        if po.status not in ('draft',):
            return Response(
                {"detail": "Can only add lines to a draft PO."},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = POLineItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        line = serializer.save(purchase_order=po)
        po.recalculate_total()
        return Response(
            POLineItemSerializer(line).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        """Submit PO for procurement."""
        po = self.get_object()
        if po.status != 'draft':
            return Response(
                {"detail": f"Cannot submit a PO with status '{po.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not po.line_items.exists():
            return Response(
                {"detail": "Cannot submit an empty PO."},
                status=status.HTTP_400_BAD_REQUEST
            )
        po.status = 'submitted'
        po.save()
        return Response(PurchaseOrderSerializer(po, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """Approve a submitted PO."""
        po = self.get_object()
        if po.status != 'submitted':
            return Response(
                {"detail": f"Cannot approve a PO with status '{po.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        po.status      = 'approved'
        po.approved_by = request.user
        po.approved_at = timezone.now()
        po.save()
        return Response(PurchaseOrderSerializer(po, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='mark-ordered')
    def mark_ordered(self, request, pk=None):
        """Mark PO as ordered from supplier."""
        po = self.get_object()
        if po.status != 'approved':
            return Response(
                {"detail": f"Cannot mark as ordered a PO with status '{po.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        supplier = request.data.get('supplier', '')
        expected = request.data.get('expected_delivery')
        if supplier:
            po.supplier = supplier
        if expected:
            po.expected_delivery = expected
        po.status = 'ordered'
        po.save()
        po.line_items.filter(status='pending').update(status='ordered')
        return Response(PurchaseOrderSerializer(po, context={'request': request}).data)

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """Dashboard summary for procurement."""
        qs = PurchaseOrder.objects.all()
        return Response({
            'total':     qs.count(),
            'draft':     qs.filter(status='draft').count(),
            'submitted': qs.filter(status='submitted').count(),
            'approved':  qs.filter(status='approved').count(),
            'ordered':   qs.filter(status='ordered').count(),
            'received':  qs.filter(status='received').count(),
        })


class GoodsReceiptViewSet(viewsets.ModelViewSet):
    """
    Goods Receipts — admin/technician only.
    """
    permission_classes = [IsAdminOrTechnician]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['receipt_number', 'supplier_invoice']
    ordering           = ['-received_date']

    def get_queryset(self):
        qs     = GoodsReceipt.objects.select_related(
            'purchase_order', 'received_by'
        ).prefetch_related('items__po_line_item__catalogue_item')
        params = self.request.query_params
        if params.get('po'):
            qs = qs.filter(purchase_order_id=params['po'])
        if params.get('status'):
            qs = qs.filter(status=params['status'])
        return qs

    def get_serializer_class(self):
        return GoodsReceiptSerializer

    @action(detail=True, methods=['post'], url_path='add-item')
    def add_item(self, request, pk=None):
        """
        Add a received item to a goods receipt.
        POST /api/goods-receipts/{id}/add-item/
        """
        receipt = self.get_object()
        if receipt.status == 'confirmed':
            return Response(
                {"detail": "Cannot modify a confirmed goods receipt."},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = GoodsReceiptItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save(goods_receipt=receipt)
        return Response(
            GoodsReceiptItemSerializer(item).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        """
        Confirm goods receipt — updates PO line quantities
        and marks PO status accordingly.
        POST /api/goods-receipts/{id}/confirm/
        """
        receipt = self.get_object()
        if receipt.status == 'confirmed':
            return Response(
                {"detail": "Already confirmed."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not receipt.items.exists():
            return Response(
                {"detail": "Cannot confirm an empty goods receipt."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Update each PO line item quantity received
            for item in receipt.items.all():
                line = item.po_line_item
                line.quantity_received += item.quantity_received
                if line.quantity_received >= line.quantity_ordered:
                    line.status = 'received'
                else:
                    line.status = 'partial'
                line.save()

            # Update PO status
            po    = receipt.purchase_order
            lines = po.line_items.all()
            if all(l.status == 'received' for l in lines):
                po.status = 'received'
            else:
                po.status = 'partial'
            po.save()

            # Mark needs requests as received
            for line in lines:
                if line.consolidated_request:
                    line.consolidated_request.requests.all().update(
                        status='received'
                    )

            receipt.status = 'confirmed'
            receipt.save()

            # Auto-create or update stock items in inventory
            from apps.inventory.models import StockItem, StockMovement
            for item in receipt.items.all():
                catalogue_item = item.po_line_item.catalogue_item
                lab_room       = receipt.purchase_order.line_items.first().catalogue_item
                
                # Find the lab room from the consolidated request
                # Default to first available room if not specified
                from apps.booking.models import LabRoom
                rooms = LabRoom.objects.filter(status='available')
                if not rooms.exists():
                    continue
                lab_room = rooms.first()

                # Get or create stock item
                stock_item, created = StockItem.objects.get_or_create(
                    catalogue_item = catalogue_item,
                    lab_room       = lab_room,
                    batch_number   = item.batch_number or '',
                    defaults={
                        'quantity':          item.quantity_received,
                        'unit':              item.po_line_item.unit,
                        'storage_location':  item.storage_location,
                        'expiry_date':       item.expiry_date,
                    }
                )
                if not created:
                    stock_item.quantity += item.quantity_received
                    stock_item.save()

                # Record stock movement
                StockMovement.objects.create(
                    stock_item      = stock_item,
                    movement_type   = 'in',
                    quantity        = item.quantity_received,
                    quantity_before = stock_item.quantity - item.quantity_received,
                    quantity_after  = stock_item.quantity,
                    reference       = receipt.receipt_number,
                    notes           = f"Received via {receipt.receipt_number}",
                    performed_by    = request.user,
                )

        return Response(
            GoodsReceiptSerializer(receipt, context={'request': request}).data
        )
