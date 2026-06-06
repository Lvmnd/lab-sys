"""
views.py — Needs Request Module
Future University LIMS
API endpoints for needs requests, catalogue search, and admin approval
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, Sum
from .models import CatalogueItem, NeedsRequest, ConsolidatedRequest
from .serializers import (
    CatalogueItemSerializer, CatalogueItemSearchSerializer,
    NeedsRequestSerializer, NeedsRequestApprovalSerializer,
    ConsolidatedRequestSerializer,
)


class IsAdminOrTechnician(IsAuthenticated):
    """Allow only admin or lab technician roles."""
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.groups.filter(
            name__in=['Admin', 'Lab Technician']
        ).exists() or request.user.is_staff


class CatalogueItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Catalogue items — read only for all authenticated users.
    Supports live search for the needs request form dropdown.
    """
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['common_name', 'iupac_name', 'cas_number', 'category']
    ordering_fields    = ['common_name', 'category']
    ordering           = ['common_name']

    def get_queryset(self):
        qs = CatalogueItem.objects.filter(is_active=True)
        category = self.request.query_params.get('category')
        program  = self.request.query_params.get('program')
        if category:
            qs = qs.filter(category=category)
        if program:
            qs = qs.filter(study_programs__icontains=program)
        return qs

    def get_serializer_class(self):
        # Use lightweight serializer for search dropdown
        if self.action == 'list' and self.request.query_params.get('search'):
            return CatalogueItemSearchSerializer
        return CatalogueItemSerializer

    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """
        Live search endpoint for the needs form autocomplete.
        GET /api/catalogue/search/?q=acetic
        Returns top 10 matches.
        """
        query = request.query_params.get('q', '').strip()
        if len(query) < 2:
            return Response([])
        results = CatalogueItem.objects.filter(
            is_active=True
        ).filter(
            Q(common_name__icontains=query) |
            Q(iupac_name__icontains=query) |
            Q(cas_number__icontains=query)
        )[:10]
        return Response(CatalogueItemSearchSerializer(results, many=True).data)

    @action(detail=False, methods=['get'], url_path='categories')
    def categories(self, request):
        """Return list of all active categories."""
        cats = CatalogueItem.objects.filter(
            is_active=True
        ).values_list('category', flat=True).distinct().order_by('category')
        return Response(list(cats))


class NeedsRequestViewSet(viewsets.ModelViewSet):
    """
    Needs requests — users manage their own, admins see all.
    """
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['request_code', 'catalogue_item__common_name', 'reason']
    ordering_fields    = ['created_at', 'date_needed', 'urgency', 'status']
    ordering           = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        qs   = NeedsRequest.objects.select_related(
            'catalogue_item', 'requested_by', 'reviewed_by'
        )
        # Admin and technicians see all requests
        if user.is_staff or user.groups.filter(name__in=['Admin','Lab Technician']).exists():
            pass
        else:
            # Regular users only see their own
            qs = qs.filter(requested_by=user)

        # Optional filters
        params = self.request.query_params
        if params.get('status'):
            qs = qs.filter(status=params['status'])
        if params.get('floor'):
            qs = qs.filter(floor=params['floor'])
        if params.get('program'):
            qs = qs.filter(study_program=params['program'])
        if params.get('urgency'):
            qs = qs.filter(urgency=params['urgency'])
        return qs

    def get_serializer_class(self):
        return NeedsRequestSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdminOrTechnician()]
        return [IsAuthenticated()]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Only allow deletion of draft requests
        if instance.status != 'draft':
            return Response(
                {"detail": "Only draft requests can be deleted."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='my-requests')
    def my_requests(self, request):
        """Shortcut: current user's own requests."""
        qs = NeedsRequest.objects.filter(
            requested_by=request.user
        ).select_related('catalogue_item').order_by('-created_at')
        serializer = NeedsRequestSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """Dashboard summary counts for admin."""
        if not (request.user.is_staff or
                request.user.groups.filter(name__in=['Admin','Lab Technician']).exists()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        qs = NeedsRequest.objects.all()
        return Response({
            'total':       qs.count(),
            'submitted':   qs.filter(status='submitted').count(),
            'approved':    qs.filter(status='approved').count(),
            'rejected':    qs.filter(status='rejected').count(),
            'received':    qs.filter(status='received').count(),
            'by_floor': {
                str(f): qs.filter(floor=str(f)).count()
                for f in range(1, 6)
            },
            'by_program': {
                p: qs.filter(study_program=p).count()
                for p in ['Biomedical','Biotech','Agritech','Food','Pharmacy','Medicine']
            },
        })


class ConsolidatedRequestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Consolidated requests — admin view for procurement decisions.
    """
    permission_classes = [IsAdminOrTechnician]
    ordering           = ['-consolidated_at']

    def get_queryset(self):
        return ConsolidatedRequest.objects.select_related(
            'catalogue_item', 'reviewed_by'
        ).prefetch_related('requests__requested_by')

    def get_serializer_class(self):
        return ConsolidatedRequestSerializer

    @action(detail=False, methods=['post'], url_path='consolidate')
    def consolidate(self, request):
        """
        Consolidation engine — groups all submitted NeedsRequests
        by catalogue item and creates ConsolidatedRequest records.
        POST /api/consolidated/consolidate/
        """
        submitted = NeedsRequest.objects.filter(status='submitted')
        if not submitted.exists():
            return Response(
                {"detail": "No submitted requests to consolidate."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Group by catalogue item
        item_ids = submitted.values_list(
            'catalogue_item_id', flat=True
        ).distinct()

        created_count  = 0
        updated_count  = 0

        for item_id in item_ids:
            item_requests = submitted.filter(catalogue_item_id=item_id)
            total_qty = item_requests.aggregate(
                total=Sum('quantity_requested')
            )['total'] or 0
            unit = item_requests.first().unit

            # Update existing pending consolidated or create new
            consolidated, created = ConsolidatedRequest.objects.get_or_create(
                catalogue_item_id=item_id,
                status='pending',
                defaults={
                    'total_quantity': total_qty,
                    'unit': unit,
                }
            )
            if not created:
                consolidated.total_quantity = total_qty
                consolidated.save()
                updated_count += 1
            else:
                created_count += 1

            # Link all submitted requests to this consolidated record
            consolidated.requests.set(item_requests)

            # Mark individual requests as consolidated
            item_requests.update(status='consolidated')

        return Response({
            "detail": f"Consolidation complete.",
            "created": created_count,
            "updated": updated_count,
            "total_items": created_count + updated_count,
        })

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """
        Admin approves, partially approves, or rejects a consolidated request.
        POST /api/consolidated/{id}/approve/
        """
        consolidated = self.get_object()

        if consolidated.status not in ('pending',):
            return Response(
                {"detail": f"Cannot review a request with status '{consolidated.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = NeedsRequestApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        action_type       = data['action']
        approved_qty      = data.get('approved_quantity')
        admin_notes       = data.get('admin_notes', '')
        rejection_reason  = data.get('rejection_reason', '')

        now = timezone.now()

        if action_type == 'approve':
            consolidated.status            = 'approved'
            consolidated.approved_quantity = consolidated.total_quantity
            consolidated.requests.all().update(
                status='approved',
                quantity_approved=None,  # Full quantity approved
                reviewed_at=now,
                reviewed_by=request.user,
            )

        elif action_type == 'partial':
            consolidated.status            = 'partial'
            consolidated.approved_quantity = approved_qty
            consolidated.requests.all().update(
                status='partial',
                reviewed_at=now,
                reviewed_by=request.user,
            )

        elif action_type == 'reject':
            consolidated.status = 'rejected'
            consolidated.requests.all().update(
                status='rejected',
                rejection_reason=rejection_reason,
                reviewed_at=now,
                reviewed_by=request.user,
            )

        consolidated.admin_notes  = admin_notes
        consolidated.reviewed_by  = request.user
        consolidated.reviewed_at  = now
        consolidated.save()

        return Response(
            ConsolidatedRequestSerializer(consolidated).data,
            status=status.HTTP_200_OK
        )