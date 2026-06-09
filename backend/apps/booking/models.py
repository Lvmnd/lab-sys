"""
models.py — Booking Module
Future University LIMS
Manages lab room and equipment reservations for all 5 floors
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid


class LabRoom(models.Model):
    """
    A physical lab room in the building.
    Each room belongs to a floor and has a type and capacity.
    """
    FLOOR_CHOICES = [
        ('APU', 'APU Building'),
        ('1',   'Floor 1 — Teaching Lab (New Building)'),
        ('2',   'Floor 2 — Teaching Lab (New Building)'),
        ('3',   'Floor 3 — Teaching Lab (New Building)'),
        ('4',   'Floor 4 — Research Lab (New Building)'),
        ('5',   'Floor 5 — Office (New Building)'),
    ]
    TYPE_CHOICES = [
        ('teaching',    'Teaching Laboratory'),
        ('research',    'Research Laboratory'),
        ('instrument',  'Instrument Room'),
        ('cold',        'Cold Room'),
        ('culture',     'Cell Culture Room'),
        ('prep',        'Preparation Room'),
        ('office',      'Office'),
        ('storage',     'Storage Room'),
    ]
    STATUS_CHOICES = [
        ('available',    'Available'),
        ('maintenance',  'Under Maintenance'),
        ('reserved',     'Permanently Reserved'),
        ('inactive',     'Inactive'),
    ]
    PROGRAM_CHOICES = [
        ('Biomedical',  'Biomedical'),
        ('Biotech',     'Biotechnology'),
        ('Agritech',    'Agricultural Technology'),
        ('Food',        'Food Technology'),
        ('Pharmacy',    'Pharmacy'),
        ('Medicine',    'Medicine'),
        ('General',     'General / Shared'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_code       = models.CharField(max_length=20, unique=True)
    name            = models.CharField(max_length=100)
    floor           = models.CharField(max_length=3, choices=FLOOR_CHOICES)
    room_type       = models.CharField(max_length=20, choices=TYPE_CHOICES, default='teaching')
    capacity        = models.PositiveIntegerField(default=30, help_text="Max number of people")
    study_program   = models.CharField(max_length=50, choices=PROGRAM_CHOICES, default='General')
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    description     = models.TextField(blank=True)
    facilities      = models.TextField(blank=True, help_text="Comma-separated list of facilities")
    responsible_technician = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='responsible_rooms'
    )
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['floor', 'room_code']
        verbose_name = 'Lab Room'
        verbose_name_plural = 'Lab Rooms'

    def __str__(self):
        return f"{self.room_code} — {self.name} (Floor {self.floor})"

    @property
    def is_bookable(self):
        return self.status == 'available'


class Equipment(models.Model):
    """
    A piece of equipment or instrument inside a lab room.
    Can be booked independently from the room.
    """
    STATUS_CHOICES = [
        ('available',   'Available'),
        ('in_use',      'In Use'),
        ('maintenance', 'Under Maintenance'),
        ('broken',      'Out of Service'),
        ('retired',     'Retired'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    equipment_code  = models.CharField(max_length=20, unique=True)
    name            = models.CharField(max_length=150)
    brand           = models.CharField(max_length=100, blank=True)
    model_number    = models.CharField(max_length=100, blank=True)
    serial_number   = models.CharField(max_length=100, blank=True, unique=True, null=True)
    lab_room        = models.ForeignKey(
        LabRoom, on_delete=models.PROTECT, related_name='equipment'
    )
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    description     = models.TextField(blank=True)
    requires_training = models.BooleanField(default=False, help_text="User needs training before use")
    max_booking_hours = models.PositiveIntegerField(default=8, help_text="Max hours per booking")
    next_maintenance  = models.DateField(null=True, blank=True)
    purchased_date    = models.DateField(null=True, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['lab_room__floor', 'name']
        verbose_name = 'Equipment'
        verbose_name_plural = 'Equipment'

    def __str__(self):
        return f"{self.equipment_code} — {self.name} ({self.lab_room.room_code})"

    @property
    def is_bookable(self):
        return self.status == 'available'

    @property
    def maintenance_due(self):
        if not self.next_maintenance:
            return False
        return self.next_maintenance <= timezone.now().date()


class Booking(models.Model):
    """
    A reservation for a lab room and/or equipment.
    Supports conflict detection and approval workflow.
    """
    STATUS_CHOICES = [
        ('pending',   'Pending Approval'),
        ('approved',  'Approved'),
        ('rejected',  'Rejected'),
        ('cancelled', 'Cancelled'),
        ('ongoing',   'Ongoing'),
        ('completed', 'Completed'),
        ('no_show',   'No Show'),
    ]
    PURPOSE_CHOICES = [
        ('class',       'Practical Class'),
        ('research',    'Research'),
        ('analysis',    'Sample Analysis'),
        ('training',    'Equipment Training'),
        ('maintenance', 'Maintenance'),
        ('other',       'Other'),
    ]
    PROGRAM_CHOICES = [
        ('Biomedical',  'Biomedical'),
        ('Biotech',     'Biotechnology'),
        ('Agritech',    'Agricultural Technology'),
        ('Food',        'Food Technology'),
        ('Pharmacy',    'Pharmacy'),
        ('Medicine',    'Medicine'),
        ('General',     'General'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_code    = models.CharField(max_length=30, unique=True, editable=False)
    booked_by       = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='bookings'
    )
    lab_room        = models.ForeignKey(
        LabRoom, on_delete=models.PROTECT,
        related_name='bookings', null=True, blank=True
    )
    equipment       = models.ForeignKey(
        Equipment, on_delete=models.PROTECT,
        related_name='bookings', null=True, blank=True
    )
    start_time      = models.DateTimeField()
    end_time        = models.DateTimeField()
    purpose         = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    study_program   = models.CharField(max_length=50, choices=PROGRAM_CHOICES)
    participant_count = models.PositiveIntegerField(default=1)
    notes           = models.TextField(blank=True)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True)
    approved_by     = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_bookings'
    )
    approved_at     = models.DateTimeField(null=True, blank=True)
    is_recurring    = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=100, blank=True,
                                        help_text="e.g. WEEKLY:13 = every week for 13 weeks")
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'

    def __str__(self):
        target = self.lab_room or self.equipment
        return f"{self.booking_code} — {target} — {self.booked_by.username}"

    def save(self, *args, **kwargs):
        if not self.booking_code:
            import datetime
            year = datetime.date.today().year
            last = Booking.objects.filter(
                booking_code__startswith=f'BK-{year}-'
            ).count()
            self.booking_code = f'BK-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    def clean(self):
        if not self.lab_room and not self.equipment:
            raise ValidationError("Booking must have either a lab room or equipment.")
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError("End time must be after start time.")
            duration = (self.end_time - self.start_time).total_seconds() / 3600
            if duration > 24:
                raise ValidationError("Booking cannot exceed 24 hours.")

    @property
    def duration_hours(self):
        if self.start_time and self.end_time:
            return round((self.end_time - self.start_time).total_seconds() / 3600, 1)
        return 0

    @property
    def is_active(self):
        return self.status in ('approved', 'ongoing')


class MaintenanceSchedule(models.Model):
    """
    Planned maintenance periods that block bookings automatically.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lab_room    = models.ForeignKey(
        LabRoom, on_delete=models.CASCADE,
        related_name='maintenance_schedules', null=True, blank=True
    )
    equipment   = models.ForeignKey(
        Equipment, on_delete=models.CASCADE,
        related_name='maintenance_schedules', null=True, blank=True
    )
    title       = models.CharField(max_length=200)
    start_time  = models.DateTimeField()
    end_time    = models.DateTimeField()
    notes       = models.TextField(blank=True)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_time']
        verbose_name = 'Maintenance Schedule'
        verbose_name_plural = 'Maintenance Schedules'

    def __str__(self):
        target = self.lab_room or self.equipment
        return f"Maintenance: {target} — {self.title}"
