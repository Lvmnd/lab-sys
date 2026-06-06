"""
admin.py — Booking Module
Future University LIMS
Registers booking models with Django admin panel
"""

from django.contrib import admin
from .models import LabRoom, Equipment, Booking, MaintenanceSchedule


@admin.register(LabRoom)
class LabRoomAdmin(admin.ModelAdmin):
    list_display  = ['room_code', 'name', 'floor', 'room_type',
                     'study_program', 'capacity', 'status']
    list_filter   = ['floor', 'room_type', 'study_program', 'status']
    search_fields = ['room_code', 'name', 'description']
    ordering      = ['floor', 'room_code']


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display  = ['equipment_code', 'name', 'brand',
                     'lab_room', 'status', 'requires_training',
                     'next_maintenance']
    list_filter   = ['status', 'requires_training', 'lab_room__floor']
    search_fields = ['equipment_code', 'name', 'brand', 'serial_number']
    ordering      = ['lab_room__floor', 'name']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display  = ['booking_code', 'booked_by', 'lab_room',
                     'equipment', 'start_time', 'end_time',
                     'purpose', 'status']
    list_filter   = ['status', 'purpose', 'study_program',
                     'lab_room__floor']
    search_fields = ['booking_code', 'booked_by__username', 'notes']
    ordering      = ['-start_time']
    readonly_fields = ['booking_code', 'created_at', 'updated_at']


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display  = ['title', 'lab_room', 'equipment',
                     'start_time', 'end_time', 'created_by']
    list_filter   = ['lab_room__floor']
    search_fields = ['title', 'notes']
    ordering      = ['start_time']
