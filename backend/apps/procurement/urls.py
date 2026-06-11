"""
urls.py — Procurement Module
Future University LIMS
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PurchaseOrderViewSet, GoodsReceiptViewSet

router = DefaultRouter()
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-orders')
router.register(r'goods-receipts',  GoodsReceiptViewSet,  basename='goods-receipts')

urlpatterns = [
    path('api/', include(router.urls)),
]
