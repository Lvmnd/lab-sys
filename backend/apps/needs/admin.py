"""
admin.py — Needs Request Module
Future University LIMS
Registers models with Django admin panel
"""

from django.contrib import admin
from .models import CatalogueItem, NeedsRequest, ConsolidatedRequest


@admin.register(CatalogueItem)
class CatalogueItemAdmin(admin.ModelAdmin):
    list_display  = ['item_code', 'common_name', 'category', 'unit',
                     'cas_number', 'storage_condition', 'is_active']
    list_filter   = ['category', 'is_active']
    search_fields = ['common_name', 'cas_number', 'iupac_name']
    ordering      = ['common_name']


@admin.register(NeedsRequest)
class NeedsRequestAdmin(admin.ModelAdmin):
    list_display  = ['request_code', 'catalogue_item', 'requested_by',
                     'quantity_requested', 'unit', 'floor',
                     'study_program', 'urgency', 'status', 'created_at']
    list_filter   = ['status', 'floor', 'study_program', 'urgency']
    search_fields = ['request_code', 'catalogue_item__common_name']
    ordering      = ['-created_at']
    readonly_fields = ['request_code', 'created_at', 'updated_at']


@admin.register(ConsolidatedRequest)
class ConsolidatedRequestAdmin(admin.ModelAdmin):
    list_display  = ['catalogue_item', 'total_quantity', 'unit',
                     'request_count', 'status', 'consolidated_at']
    list_filter   = ['status']
    search_fields = ['catalogue_item__common_name']
    ordering      = ['-consolidated_at']
