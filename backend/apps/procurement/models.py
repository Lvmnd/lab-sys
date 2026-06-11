"""
models.py — Procurement Module
Future University LIMS
Handles Purchase Orders and Goods Receipt from approved needs requests
"""

from django.db import models
from django.contrib.auth.models import User
from apps.needs.models import ConsolidatedRequest, CatalogueItem
import uuid


class PurchaseOrder(models.Model):
    """
    A formal purchase order generated from approved consolidated requests.
    One PO can contain multiple line items.
    """
    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('submitted', 'Submitted to Procurement'),
        ('approved',  'Approved'),
        ('ordered',   'Ordered from Supplier'),
        ('partial',   'Partially Received'),
        ('received',  'Fully Received'),
        ('cancelled', 'Cancelled'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    po_number    = models.CharField(max_length=30, unique=True, editable=False)
    title        = models.CharField(max_length=200)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    supplier     = models.CharField(max_length=200, blank=True)
    notes        = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_by   = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='purchase_orders'
    )
    approved_by  = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_pos'
    )
    approved_at  = models.DateTimeField(null=True, blank=True)
    expected_delivery = models.DateField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'

    def __str__(self):
        return f"{self.po_number} — {self.title}"

    def save(self, *args, **kwargs):
        if not self.po_number:
            import datetime
            year = datetime.date.today().year
            last = PurchaseOrder.objects.filter(
                po_number__startswith=f'PO-{year}-'
            ).count()
            self.po_number = f'PO-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    def recalculate_total(self):
        total = sum(
            (item.unit_price * item.quantity_ordered)
            for item in self.line_items.all()
            if item.unit_price
        )
        self.total_amount = total
        self.save()


class POLineItem(models.Model):
    """
    A single item line in a Purchase Order.
    Linked to a CatalogueItem and optionally to a ConsolidatedRequest.
    """
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('ordered',  'Ordered'),
        ('partial',  'Partially Received'),
        ('received', 'Fully Received'),
        ('cancelled','Cancelled'),
    ]

    id                   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase_order       = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name='line_items'
    )
    catalogue_item       = models.ForeignKey(
        CatalogueItem, on_delete=models.PROTECT, related_name='po_lines'
    )
    consolidated_request = models.ForeignKey(
        ConsolidatedRequest, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='po_lines'
    )
    quantity_ordered     = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_received    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit                 = models.CharField(max_length=30)
    unit_price           = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes                = models.TextField(blank=True)
    created_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['catalogue_item__common_name']
        verbose_name = 'PO Line Item'
        verbose_name_plural = 'PO Line Items'

    def __str__(self):
        return f"{self.purchase_order.po_number} — {self.catalogue_item.common_name}"

    @property
    def total_price(self):
        if self.unit_price:
            return self.unit_price * self.quantity_ordered
        return 0

    @property
    def is_fully_received(self):
        return self.quantity_received >= self.quantity_ordered


class GoodsReceipt(models.Model):
    """
    Records the arrival of items against a Purchase Order.
    Automatically updates stock when confirmed.
    """
    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt_number  = models.CharField(max_length=30, unique=True, editable=False)
    purchase_order  = models.ForeignKey(
        PurchaseOrder, on_delete=models.PROTECT, related_name='receipts'
    )
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    received_by     = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='goods_receipts'
    )
    received_date   = models.DateField()
    supplier_invoice = models.CharField(max_length=100, blank=True)
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-received_date']
        verbose_name = 'Goods Receipt'
        verbose_name_plural = 'Goods Receipts'

    def __str__(self):
        return f"{self.receipt_number} — {self.purchase_order.po_number}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            import datetime
            year = datetime.date.today().year
            last = GoodsReceipt.objects.filter(
                receipt_number__startswith=f'GR-{year}-'
            ).count()
            self.receipt_number = f'GR-{year}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)


class GoodsReceiptItem(models.Model):
    """
    Individual item received in a Goods Receipt.
    On confirmation, updates POLineItem.quantity_received
    and creates/updates StockItem (handled in inventory module).
    """
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goods_receipt   = models.ForeignKey(
        GoodsReceipt, on_delete=models.CASCADE, related_name='items'
    )
    po_line_item    = models.ForeignKey(
        POLineItem, on_delete=models.PROTECT, related_name='receipt_items'
    )
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2)
    batch_number    = models.CharField(max_length=100, blank=True)
    expiry_date     = models.DateField(null=True, blank=True)
    storage_location = models.CharField(max_length=200, blank=True)
    condition       = models.CharField(
        max_length=20,
        choices=[('good','Good'),('damaged','Damaged'),('rejected','Rejected')],
        default='good'
    )
    notes           = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Goods Receipt Item'
        verbose_name_plural = 'Goods Receipt Items'

    def __str__(self):
        return f"{self.goods_receipt.receipt_number} — {self.po_line_item.catalogue_item.common_name}"
