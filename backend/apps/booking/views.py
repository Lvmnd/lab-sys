"""
views.py — Booking Module
Future University LIMS
API endpoints for lab room and equipment booking
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Count
import datetime

from .models import LabRoom, Equipment, Booking, MaintenanceSchedule
from .serializers import (
    LabRoomSerializer, LabRoomBriefSerializer,
    EquipmentSerializer, EquipmentBriefSerializer,
    BookingSerializer, BookingApprovalSerializer,
    MaintenanceScheduleSerializer,
)


class IsAdminOrTechnician(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.groups.filter(
            name__in=['Admin', 'Lab Technician']
        ).exists() or request.user.is_staff


class LabRoomViewSet(viewsets.ModelViewSet):
    """
    Lab rooms — read for all, write for admin/technician only.
    """
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['room_code', 'name', 'description']
    ordering_fields    = ['floor', 'room_code', 'name']
    ordering           = ['floor', 'room_code']

    def get_queryset(self):
        qs = LabRoom.objects.prefetch_related('equipment')
        params = self.request.query_params
        if params.get('floor'):
            qs = qs.filter(floor=params['floor'])
        if params.get('program'):
            qs = qs.filter(
                Q(study_program=params['program']) |
                Q(study_program='General')
            )
        if params.get('status'):
            qs = qs.filter(status=params['status'])
        if params.get('available_only') == 'true':
            qs = qs.filter(status='available')
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return LabRoomBriefSerializer
        return LabRoomSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrTechnician()]
        return []

    @action(detail=True, methods=['get'], url_path='availability')
    def availability(self, request, pk=None):
        """
        Get booked slots for a room on a specific date.
        GET /api/rooms/{id}/availability/?date=2025-09-01
        """
        room = self.get_object()
        date_str = request.query_params.get('date')
        if not date_str:
            return Response(
                {"detail": "date parameter required (YYYY-MM-DD)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            date = datetime.date.fromisoformat(date_str)
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        bookings = Booking.objects.filter(
            lab_room=room,
            status__in=['pending', 'approved', 'ongoing'],
            start_time__date=date,
        ).values('booking_code', 'start_time', 'end_time', 'purpose', 'status')

        maintenance = MaintenanceSchedule.objects.filter(
            lab_room=room,
            start_time__date__lte=date,
            end_time__date__gte=date,
        ).values('title', 'start_time', 'end_time')

        return Response({
            "room":        str(room),
            "date":        date_str,
            "is_bookable": room.is_bookable,
            "bookings":    list(bookings),
            "maintenance": list(maintenance),
        })

    @action(detail=False, methods=['get'], url_path='by-floor')
    def by_floor(self, request):
        """
        Returns rooms grouped by floor.
        GET /api/rooms/by-floor/
        """
        result = {}
        for floor_val, floor_label in LabRoom.FLOOR_CHOICES:
            rooms = LabRoom.objects.filter(floor=floor_val)
            result[floor_label] = LabRoomBriefSerializer(rooms, many=True).data
        return Response(result)


class EquipmentViewSet(viewsets.ModelViewSet):
    """
    Equipment — read for all, write for admin/technician only.
    """
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['equipment_code', 'name', 'brand', 'model_number', 'serial_number']
    ordering_fields    = ['name', 'status']
    ordering           = ['lab_room__floor', 'name']

    def get_queryset(self):
        qs = Equipment.objects.select_related('lab_room')
        params = self.request.query_params
        if params.get('room'):
            qs = qs.filter(lab_room_id=params['room'])
        if params.get('floor'):
            qs = qs.filter(lab_room__floor=params['floor'])
        if params.get('available_only') == 'true':
            qs = qs.filter(status='available')
        if params.get('maintenance_due') == 'true':
            qs = qs.filter(next_maintenance__lte=timezone.now().date())
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return EquipmentBriefSerializer
        return EquipmentSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrTechnician()]
        return []

    @action(detail=True, methods=['get'], url_path='availability')
    def availability(self, request, pk=None):
        """
        Get booked slots for equipment on a specific date.
        GET /api/equipment/{id}/availability/?date=2025-09-01
        """
        equip = self.get_object()
        date_str = request.query_params.get('date')
        if not date_str:
            return Response(
                {"detail": "date parameter required (YYYY-MM-DD)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            date = datetime.date.fromisoformat(date_str)
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        bookings = Booking.objects.filter(
            equipment=equip,
            status__in=['pending', 'approved', 'ongoing'],
            start_time__date=date,
        ).values('booking_code', 'start_time', 'end_time', 'purpose', 'status')

        return Response({
            "equipment":       str(equip),
            "date":            date_str,
            "is_bookable":     equip.is_bookable,
            "max_hours":       equip.max_booking_hours,
            "maintenance_due": equip.maintenance_due,
            "bookings":        list(bookings),
        })


class BookingViewSet(viewsets.ModelViewSet):
    """
    Bookings — users manage their own, admin/technician see all.
    """
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['booking_code', 'notes']
    ordering_fields    = ['start_time', 'created_at', 'status']
    ordering           = ['-start_time']

    def get_queryset(self):
        user = self.request.user
        qs   = Booking.objects.select_related(
            'booked_by', 'approved_by', 'lab_room', 'equipment'
        )
        # Admin and technician see all
        if not (user.is_staff or
                user.groups.filter(name__in=['Admin', 'Lab Technician']).exists()):
            qs = qs.filter(booked_by=user)

        params = self.request.query_params
        if params.get('status'):
            qs = qs.filter(status=params['status'])
        if params.get('floor'):
            qs = qs.filter(lab_room__floor=params['floor'])
        if params.get('room'):
            qs = qs.filter(lab_room_id=params['room'])
        if params.get('date'):
            try:
                date = datetime.date.fromisoformat(params['date'])
                qs   = qs.filter(start_time__date=date)
            except ValueError:
                pass
        if params.get('upcoming') == 'true':
            qs = qs.filter(start_time__gte=timezone.now())
        return qs

    def get_serializer_class(self):
        return BookingSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrTechnician()]
        return []

    def destroy(self, request, *args, **kwargs):
        booking = self.get_object()
        if booking.status not in ('pending',):
            return Response(
                {"detail": "Only pending bookings can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST
            )
        booking.status = 'cancelled'
        booking.save()
        return Response(
            {"detail": f"Booking {booking.booking_code} cancelled."},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], url_path='my-bookings')
    def my_bookings(self, request):
        """Current user's upcoming bookings."""
        qs = Booking.objects.filter(
            booked_by=request.user,
            start_time__gte=timezone.now(),
        ).select_related('lab_room', 'equipment').order_by('start_time')
        return Response(BookingSerializer(qs, many=True, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """
        Technician or admin approves or rejects a booking.
        POST /api/bookings/{id}/approve/
        """
        if not (request.user.is_staff or
                request.user.groups.filter(name__in=['Admin', 'Lab Technician']).exists()):
            return Response(status=status.HTTP_403_FORBIDDEN)

        booking = self.get_object()
        if booking.status != 'pending':
            return Response(
                {"detail": f"Cannot review a booking with status '{booking.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BookingApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if data['action'] == 'approve':
            booking.status      = 'approved'
            booking.approved_by = request.user
            booking.approved_at = timezone.now()
        else:
            booking.status           = 'rejected'
            booking.rejection_reason = data['rejection_reason']

        booking.save()
        return Response(
            BookingSerializer(booking, context={'request': request}).data
        )

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """Dashboard summary for admin."""
        if not (request.user.is_staff or
                request.user.groups.filter(name__in=['Admin', 'Lab Technician']).exists()):
            return Response(status=status.HTTP_403_FORBIDDEN)

        today = timezone.now().date()
        qs    = Booking.objects.all()

        return Response({
            'total':          qs.count(),
            'pending':        qs.filter(status='pending').count(),
            'approved':       qs.filter(status='approved').count(),
            'today':          qs.filter(start_time__date=today).count(),
            'this_week':      qs.filter(
                start_time__date__gte=today,
                start_time__date__lte=today + datetime.timedelta(days=7)
            ).count(),
            'by_floor': {
                str(f): qs.filter(lab_room__floor=str(f)).count()
                for f in range(1, 6)
            },
            'by_purpose': {
                p[0]: qs.filter(purpose=p[0]).count()
                for p in Booking.PURPOSE_CHOICES
            },
        })

    @action(detail=False, methods=['get'], url_path='calendar')
    def calendar(self, request):
        """
        Returns all approved bookings for a date range.
        Used to populate the calendar view on the frontend.
        GET /api/bookings/calendar/?start=2025-09-01&end=2025-09-30
        """
        start_str = request.query_params.get('start')
        end_str   = request.query_params.get('end')

        if not start_str or not end_str:
            return Response(
                {"detail": "start and end date parameters required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            start = datetime.date.fromisoformat(start_str)
            end   = datetime.date.fromisoformat(end_str)
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        bookings = Booking.objects.filter(
            status__in=['approved', 'ongoing', 'pending'],
            start_time__date__gte=start,
            start_time__date__lte=end,
        ).select_related('booked_by', 'lab_room', 'equipment')

        # Format for calendar display
        events = []
        for b in bookings:
            target = b.lab_room.name if b.lab_room else b.equipment.name
            events.append({
                'id':           str(b.id),
                'booking_code': b.booking_code,
                'title':        f"{target} — {b.get_purpose_display()}",
                'start':        b.start_time.isoformat(),
                'end':          b.end_time.isoformat(),
                'status':       b.status,
                'booked_by':    b.booked_by.get_full_name() or b.booked_by.username,
                'floor':        b.lab_room.floor if b.lab_room else None,
                'room':         b.lab_room.room_code if b.lab_room else None,
                'equipment':    b.equipment.equipment_code if b.equipment else None,
            })
        return Response(events)


class MaintenanceScheduleViewSet(viewsets.ModelViewSet):
    """
    Maintenance schedules — admin/technician only.
    """
    permission_classes = [IsAdminOrTechnician]
    serializer_class   = MaintenanceScheduleSerializer
    ordering           = ['start_time']

    def get_queryset(self):
        qs = MaintenanceSchedule.objects.select_related(
            'lab_room', 'equipment', 'created_by'
        )
        params = self.request.query_params
        if params.get('room'):
            qs = qs.filter(lab_room_id=params['room'])
        if params.get('equipment'):
            qs = qs.filter(equipment_id=params['equipment'])
        if params.get('upcoming') == 'true':
            qs = qs.filter(end_time__gte=timezone.now())
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
