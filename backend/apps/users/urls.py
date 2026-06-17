"""
urls.py — Users Module
Future University LIMS
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

router = DefaultRouter()
router.register(r'auth/users', UserViewSet, basename='users')

urlpatterns = [
    path('api/', include(router.urls)),
]
