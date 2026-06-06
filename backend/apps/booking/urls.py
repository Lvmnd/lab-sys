"""
urls.py — Booking Module
Future University LIMS
API URL routing for rooms, equipment, bookings, and maintenance
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LabRoomViewSet,
    EquipmentViewSet,
    BookingViewSet,
    MaintenanceScheduleViewSet,
)

router = DefaultRouter()
router.register(r'rooms',       LabRoomViewSet,            basename='rooms')
router.register(r'equipment',   EquipmentViewSet,          basename='equipment')
router.register(r'bookings',    BookingViewSet,            basename='bookings')
router.register(r'maintenance', MaintenanceScheduleViewSet, basename='maintenance')

urlpatterns = [
    path('api/', include(router.urls)),
]
