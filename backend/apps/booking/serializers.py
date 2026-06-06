"""
serializers.py — Booking Module
Future University LIMS
Converts booking models to/from JSON for the REST API
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .models import LabRoom, Equipment, Booking, MaintenanceSchedule
import datetime


class UserBriefSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ['id', 'username', 'full_name', 'email']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class EquipmentBriefSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source='lab_room.name', read_only=True)
    room_code = serializers.CharField(source='lab_room.room_code', read_only=True)
    floor     = serializers.CharField(source='lab_room.floor', read_only=True)

    class Meta:
        model  = Equipment
        fields = [
            'id', 'equipment_code', 'name', 'brand', 'model_number',
            'status', 'requires_training', 'max_booking_hours',
            'room_name', 'room_code', 'floor', 'maintenance_due',
        ]


class EquipmentSerializer(serializers.ModelSerializer):
    lab_room        = serializers.StringRelatedField(read_only=True)
    lab_room_id     = serializers.UUIDField(write_only=True)
    is_bookable     = serializers.ReadOnlyField()
    maintenance_due = serializers.ReadOnlyField()
    status_display  = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model  = Equipment
        fields = [
            'id', 'equipment_code', 'name', 'brand', 'model_number',
            'serial_number', 'lab_room', 'lab_room_id',
            'status', 'status_display', 'description',
            'requires_training', 'max_booking_hours',
            'next_maintenance', 'purchased_date',
            'is_bookable', 'maintenance_due',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LabRoomSerializer(serializers.ModelSerializer):
    equipment           = EquipmentBriefSerializer(many=True, read_only=True)
    equipment_count     = serializers.SerializerMethodField()
    responsible_technician = UserBriefSerializer(read_only=True)
    is_bookable         = serializers.ReadOnlyField()
    status_display      = serializers.CharField(source='get_status_display', read_only=True)
    floor_display       = serializers.CharField(source='get_floor_display', read_only=True)
    type_display        = serializers.CharField(source='get_room_type_display', read_only=True)
    program_display     = serializers.CharField(source='get_study_program_display', read_only=True)

    class Meta:
        model  = LabRoom
        fields = [
            'id', 'room_code', 'name', 'floor', 'floor_display',
            'room_type', 'type_display', 'capacity',
            'study_program', 'program_display',
            'status', 'status_display',
            'description', 'facilities',
            'responsible_technician',
            'equipment', 'equipment_count',
            'is_bookable', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_equipment_count(self, obj):
        return obj.equipment.filter(status='available').count()


class LabRoomBriefSerializer(serializers.ModelSerializer):
    """Lightweight serializer for booking form dropdowns."""
    floor_display   = serializers.CharField(source='get_floor_display', read_only=True)
    program_display = serializers.CharField(source='get_study_program_display', read_only=True)

    class Meta:
        model  = LabRoom
        fields = [
            'id', 'room_code', 'name', 'floor', 'floor_display',
            'room_type', 'capacity', 'study_program', 'program_display',
            'status', 'is_bookable',
        ]


class MaintenanceScheduleSerializer(serializers.ModelSerializer):
    created_by = UserBriefSerializer(read_only=True)

    class Meta:
        model  = MaintenanceSchedule
        fields = [
            'id', 'lab_room', 'equipment', 'title',
            'start_time', 'end_time', 'notes',
            'created_by', 'created_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at']


class BookingSerializer(serializers.ModelSerializer):
    booked_by       = UserBriefSerializer(read_only=True)
    approved_by     = UserBriefSerializer(read_only=True)
    lab_room        = LabRoomBriefSerializer(read_only=True)
    lab_room_id     = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    equipment       = EquipmentBriefSerializer(read_only=True)
    equipment_id    = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    status_display  = serializers.CharField(source='get_status_display', read_only=True)
    purpose_display = serializers.CharField(source='get_purpose_display', read_only=True)
    program_display = serializers.CharField(source='get_study_program_display', read_only=True)
    duration_hours  = serializers.ReadOnlyField()
    is_active       = serializers.ReadOnlyField()

    class Meta:
        model  = Booking
        fields = [
            'id', 'booking_code',
            'booked_by', 'approved_by',
            'lab_room', 'lab_room_id',
            'equipment', 'equipment_id',
            'start_time', 'end_time', 'duration_hours',
            'purpose', 'purpose_display',
            'study_program', 'program_display',
            'participant_count', 'notes',
            'status', 'status_display',
            'rejection_reason',
            'is_recurring', 'recurrence_rule',
            'approved_at', 'created_at', 'updated_at',
            'is_active',
        ]
        read_only_fields = [
            'id', 'booking_code', 'booked_by', 'approved_by',
            'rejection_reason', 'approved_at',
            'created_at', 'updated_at',
        ]

    def validate(self, data):
        start = data.get('start_time')
        end   = data.get('end_time')
        room_id  = data.get('lab_room_id')
        equip_id = data.get('equipment_id')

        # Must book at least one
        if not room_id and not equip_id:
            raise serializers.ValidationError(
                "Must select at least a lab room or equipment."
            )

        # Time validation
        if start and end:
            if end <= start:
                raise serializers.ValidationError(
                    {"end_time": "End time must be after start time."}
                )
            if start < timezone.now():
                raise serializers.ValidationError(
                    {"start_time": "Cannot book in the past."}
                )
            duration = (end - start).total_seconds() / 3600
            if duration > 24:
                raise serializers.ValidationError(
                    {"end_time": "Booking cannot exceed 24 hours."}
                )

        # Conflict detection — lab room
        if room_id and start and end:
            try:
                room = LabRoom.objects.get(id=room_id)
                if not room.is_bookable:
                    raise serializers.ValidationError(
                        {"lab_room_id": f"Room '{room.name}' is not available for booking."}
                    )
                conflict = Booking.objects.filter(
                    lab_room_id=room_id,
                    status__in=['pending', 'approved', 'ongoing'],
                ).exclude(
                    id=self.instance.id if self.instance else None
                ).filter(
                    start_time__lt=end,
                    end_time__gt=start,
                )
                if conflict.exists():
                    c = conflict.first()
                    raise serializers.ValidationError({
                        "lab_room_id": (
                            f"Room '{room.name}' is already booked from "
                            f"{c.start_time.strftime('%d %b %Y %H:%M')} to "
                            f"{c.end_time.strftime('%H:%M')} "
                            f"(Booking: {c.booking_code})."
                        )
                    })
                # Check maintenance blackout
                maintenance = MaintenanceSchedule.objects.filter(
                    lab_room_id=room_id,
                    start_time__lt=end,
                    end_time__gt=start,
                )
                if maintenance.exists():
                    m = maintenance.first()
                    raise serializers.ValidationError({
                        "lab_room_id": (
                            f"Room '{room.name}' is under maintenance: "
                            f"'{m.title}' from "
                            f"{m.start_time.strftime('%d %b %Y %H:%M')} to "
                            f"{m.end_time.strftime('%d %b %Y %H:%M')}."
                        )
                    })
                data['lab_room'] = room
            except LabRoom.DoesNotExist:
                raise serializers.ValidationError(
                    {"lab_room_id": "Lab room not found."}
                )

        # Conflict detection — equipment
        if equip_id and start and end:
            try:
                equip = Equipment.objects.get(id=equip_id)
                if not equip.is_bookable:
                    raise serializers.ValidationError(
                        {"equipment_id": f"Equipment '{equip.name}' is not available."}
                    )
                duration = (end - start).total_seconds() / 3600
                if duration > equip.max_booking_hours:
                    raise serializers.ValidationError({
                        "end_time": (
                            f"'{equip.name}' can only be booked for max "
                            f"{equip.max_booking_hours} hours at a time."
                        )
                    })
                conflict = Booking.objects.filter(
                    equipment_id=equip_id,
                    status__in=['pending', 'approved', 'ongoing'],
                ).exclude(
                    id=self.instance.id if self.instance else None
                ).filter(
                    start_time__lt=end,
                    end_time__gt=start,
                )
                if conflict.exists():
                    c = conflict.first()
                    raise serializers.ValidationError({
                        "equipment_id": (
                            f"'{equip.name}' is already booked from "
                            f"{c.start_time.strftime('%d %b %Y %H:%M')} to "
                            f"{c.end_time.strftime('%H:%M')} "
                            f"(Booking: {c.booking_code})."
                        )
                    })
                # Check maintenance blackout
                maintenance = MaintenanceSchedule.objects.filter(
                    equipment_id=equip_id,
                    start_time__lt=end,
                    end_time__gt=start,
                )
                if maintenance.exists():
                    m = maintenance.first()
                    raise serializers.ValidationError({
                        "equipment_id": (
                            f"'{equip.name}' is under maintenance: "
                            f"'{m.title}'."
                        )
                    })
                data['equipment'] = equip
            except Equipment.DoesNotExist:
                raise serializers.ValidationError(
                    {"equipment_id": "Equipment not found."}
                )

        return data

    def create(self, validated_data):
        validated_data.pop('lab_room_id', None)
        validated_data.pop('equipment_id', None)
        validated_data['booked_by'] = self.context['request'].user
        validated_data['status']    = 'pending'
        return super().create(validated_data)


class BookingApprovalSerializer(serializers.Serializer):
    """Used by technician or admin to approve or reject a booking."""
    action           = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError(
                {"rejection_reason": "Rejection reason is required."}
            )
        return data


class AvailabilitySerializer(serializers.Serializer):
    """Query parameters for checking availability."""
    date       = serializers.DateField()
    start_time = serializers.TimeField(required=False)
    end_time   = serializers.TimeField(required=False)
    floor      = serializers.CharField(required=False)
    program    = serializers.CharField(required=False)
