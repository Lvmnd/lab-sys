"""
models.py — Inventory Module
Future University LIMS
Tracks stock levels per item per lab room
"""

from django.db import models
from django.contrib.auth.models import User
from apps.needs.models import CatalogueItem
from apps.booking.models import LabRoom
import uuid


class StockItem(models.Model):
    """
    Current stock level for one catalogue item in one lab room.
    Created automatically when a Goods Receipt is confirmed.
    Updated every time stock moves.
    """
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    catalogue_item = models.ForeignKey(
        CatalogueItem, on_delete=models.PROTECT, related_name='stock_items'
    )
    lab_room       = models.ForeignKey(
        LabRoom, on_delete=models.PROTECT, related_name='stock_items'
    )
    quantity       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit           = models.CharField(max_length=30)
    min_stock      = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Alert when stock falls below this level"
    )
    batch_number   = models.CharField(max_length=100, blank=True)
    expiry_date    = models.DateField(null=True, blank=True)
    storage_location = models.CharField(max_length=200, blank=True)
    last_updated   = models.DateTimeField(auto_now=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['lab_room__floor', 'catalogue_item__common_name']
        unique_together = ['catalogue_item', 'lab_room', 'batch_number']
        verbose_name = 'Stock Item'
        verbose_name_plural = 'Stock Items'

    def __str__(self):
        return f"{self.catalogue_item.common_name} \u2014 {self.lab_room.room_code} ({self.quantity} {self.unit})"

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_stock and self.min_stock > 0

    @property
    def is_out_of_stock(self):
        return self.quantity <= 0

    @property
    def is_expiring_soon(self):
        if not self.expiry_date:
            return False
        from django.utils import timezone
        days_left = (self.expiry_date - timezone.now().date()).days
        return 0 <= days_left <= 30

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()


class StockMovement(models.Model):
    """
    Every change to stock is recorded here — in, out, adjustment.
    This is the audit trail for inventory.
    """
    MOVEMENT_TYPES = [
        ('in',          'Stock In — Goods Receipt'),
        ('out',         'Stock Out — Lab Usage'),
        ('adjustment',  'Manual Adjustment'),
        ('transfer',    'Transfer Between Labs'),
        ('expired',     'Expired / Disposed'),
        ('returned',    'Returned to Supplier'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock_item   = models.ForeignKey(
        StockItem, on_delete=models.PROTECT, related_name='movements'
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity      = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_before = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_after  = models.DecimalField(max_digits=10, decimal_places=2)
    reference     = models.CharField(
        max_length=100, blank=True,
        help_text="PO number, booking code, or other reference"
    )
    notes         = models.TextField(blank=True)
    performed_by  = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='stock_movements'
    )
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Stock Movement'
        verbose_name_plural = 'Stock Movements'

    def __str__(self):
        return f"{self.movement_type} \u2014 {self.stock_item.catalogue_item.common_name} x{self.quantity}"


class StockAlert(models.Model):
    """
    System-generated alerts for low stock and expiring items.
    Cleared when stock is replenished or item is disposed.
    """
    ALERT_TYPES = [
        ('low_stock',     'Low Stock'),
        ('out_of_stock',  'Out of Stock'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired',       'Expired'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock_item  = models.ForeignKey(
        StockItem, on_delete=models.CASCADE, related_name='alerts'
    )
    alert_type  = models.CharField(max_length=20, choices=ALERT_TYPES)
    message     = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resolved_alerts'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Stock Alert'
        verbose_name_plural = 'Stock Alerts'

    def __str__(self):
        return f"{self.alert_type} \u2014 {self.stock_item.catalogue_item.common_name}"
