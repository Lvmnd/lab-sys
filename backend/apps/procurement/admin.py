"""
admin.py — Procurement Module
Future University LIMS
"""

from django.contrib import admin
from .models import PurchaseOrder, POLineItem, GoodsReceipt, GoodsReceiptItem


class POLineItemInline(admin.TabularInline):
    model  = POLineItem
    extra  = 0
    fields = ['catalogue_item', 'quantity_ordered', 'quantity_received',
              'unit', 'unit_price', 'status']
    readonly_fields = ['quantity_received']


class GoodsReceiptItemInline(admin.TabularInline):
    model  = GoodsReceiptItem
    extra  = 0
    fields = ['po_line_item', 'quantity_received', 'batch_number',
              'expiry_date', 'storage_location', 'condition']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display    = ['po_number', 'title', 'supplier', 'status',
                       'total_amount', 'expected_delivery', 'created_at']
    list_filter     = ['status']
    search_fields   = ['po_number', 'title', 'supplier']
    ordering        = ['-created_at']
    readonly_fields = ['po_number', 'total_amount', 'created_at', 'updated_at']
    inlines         = [POLineItemInline]


@admin.register(POLineItem)
class POLineItemAdmin(admin.ModelAdmin):
    list_display  = ['purchase_order', 'catalogue_item', 'quantity_ordered',
                     'quantity_received', 'unit', 'unit_price', 'status']
    list_filter   = ['status']
    search_fields = ['catalogue_item__common_name', 'purchase_order__po_number']


@admin.register(GoodsReceipt)
class GoodsReceiptAdmin(admin.ModelAdmin):
    list_display    = ['receipt_number', 'purchase_order', 'status',
                       'received_by', 'received_date', 'created_at']
    list_filter     = ['status']
    search_fields   = ['receipt_number', 'purchase_order__po_number']
    ordering        = ['-received_date']
    readonly_fields = ['receipt_number', 'created_at', 'updated_at']
    inlines         = [GoodsReceiptItemInline]


@admin.register(GoodsReceiptItem)
class GoodsReceiptItemAdmin(admin.ModelAdmin):
    list_display  = ['goods_receipt', 'po_line_item', 'quantity_received',
                     'batch_number', 'expiry_date', 'condition']
    list_filter   = ['condition']
    search_fields = ['po_line_item__catalogue_item__common_name']
