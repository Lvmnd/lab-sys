"""
urls.py — Future University LIMS
Main URL router — connects all module APIs
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # JWT authentication
    path('api/auth/login/',   TokenObtainPairView.as_view(),  name='token_obtain'),
    path('api/auth/refresh/', TokenRefreshView.as_view(),     name='token_refresh'),

    # Needs Request module
    path('', include('apps.needs.urls')),

    # Booking module
    path('', include('apps.booking.urls')),

    # Procurement module
    path('', include('apps.procurement.urls')),

    # Inventory module
    path('', include('apps.inventory.urls')),
]
