"""
admin.py — Inventory Module
Future University LIMS
"""

from django.contrib import admin
from .models import StockItem, StockMovement, StockAlert


class StockMovementInline(admin.TabularInline):
    model   = StockMovement
    extra   = 0
    fields  = ['movement_type', 'quantity', 'quantity_before',
                'quantity_after', 'reference', 'performed_by', 'created_at']
    readonly_fields = ['quantity_before', 'quantity_after',
                       'performed_by', 'created_at']
    ordering = ['-created_at']


class StockAlertInline(admin.TabularInline):
    model   = StockAlert
    extra   = 0
    fields  = ['alert_type', 'message', 'is_resolved',
                'resolved_by', 'resolved_at']
    readonly_fields = ['resolved_by', 'resolved_at']


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display    = ['catalogue_item', 'lab_room', 'quantity',
                       'unit', 'min_stock', 'batch_number',
                       'expiry_date', 'last_updated']
    list_filter     = ['lab_room__floor', 'catalogue_item__category']
    search_fields   = ['catalogue_item__common_name',
                       'catalogue_item__cas_number',
                       'lab_room__room_code', 'batch_number']
    ordering        = ['lab_room__floor', 'catalogue_item__common_name']
    readonly_fields = ['last_updated', 'created_at']
    inlines         = [StockMovementInline, StockAlertInline]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display    = ['stock_item', 'movement_type', 'quantity',
                       'quantity_before', 'quantity_after',
                       'reference', 'performed_by', 'created_at']
    list_filter     = ['movement_type']
    search_fields   = ['stock_item__catalogue_item__common_name',
                       'reference', 'notes']
    ordering        = ['-created_at']
    readonly_fields = ['quantity_before', 'quantity_after',
                       'performed_by', 'created_at']


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display  = ['stock_item', 'alert_type', 'message',
                     'is_resolved', 'resolved_by', 'created_at']
    list_filter   = ['alert_type', 'is_resolved']
    search_fields = ['stock_item__catalogue_item__common_name', 'message']
    ordering      = ['-created_at']
    readonly_fields = ['resolved_by', 'resolved_at', 'created_at']
