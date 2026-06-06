"""
urls.py — Needs Request Module
Future University LIMS
API URL routing for catalogue, needs requests, and consolidated requests
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CatalogueItemViewSet,
    NeedsRequestViewSet,
    ConsolidatedRequestViewSet,
)

router = DefaultRouter()
router.register(r'catalogue',    CatalogueItemViewSet,      basename='catalogue')
router.register(r'needs',        NeedsRequestViewSet,       basename='needs')
router.register(r'consolidated', ConsolidatedRequestViewSet, basename='consolidated')

urlpatterns = [
    path('api/', include(router.urls)),
]
