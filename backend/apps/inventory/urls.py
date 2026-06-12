"""
urls.py — Inventory Module
Future University LIMS
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StockItemViewSet, StockMovementViewSet, StockAlertViewSet

router = DefaultRouter()
router.register(r'stock',           StockItemViewSet,     basename='stock')
router.register(r'stock-movements', StockMovementViewSet, basename='stock-movements')
router.register(r'stock-alerts',    StockAlertViewSet,    basename='stock-alerts')

urlpatterns = [
    path('api/', include(router.urls)),
]
