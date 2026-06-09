"""
models.py — Needs Request Module
Future University LIMS
Handles demand-driven procurement requests from all user types
"""

from django.db import models
from django.contrib.auth.models import User
import uuid


class CatalogueItem(models.Model):
    """
    Master item catalogue — single source of truth for all lab items.
    Seeded from lab_sys_master_catalogue_enriched.xlsx
    """
    CATEGORY_CHOICES = [
        ('Chemical',    'Chemical'),
        ('Reagent',     'Reagent'),
        ('Glassware',   'Glassware'),
        ('Instrument',  'Instrument'),
        ('Consumable',  'Consumable'),
        ('Equipment',   'Equipment'),
        ('Furniture',   'Furniture'),
        ('PPE',         'PPE'),
        ('Other',       'Other'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item_code       = models.CharField(max_length=20, unique=True)
    common_name     = models.CharField(max_length=255)
    iupac_name      = models.CharField(max_length=255, blank=True)
    cas_number      = models.CharField(max_length=20, blank=True)
    molecular_formula = models.CharField(max_length=100, blank=True)
    molecular_weight  = models.CharField(max_length=50, blank=True)
    category        = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    unit            = models.CharField(max_length=30)
    ghs_hazard_codes = models.CharField(max_length=255, blank=True)
    ghs_pictograms  = models.CharField(max_length=255, blank=True)
    storage_condition = models.CharField(max_length=100, blank=True, default='Room temperature')
    study_programs  = models.CharField(max_length=255, blank=True, help_text="Comma-separated: Biomedical,Pharmacy,etc")
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['common_name']
        verbose_name = 'Catalogue Item'
        verbose_name_plural = 'Catalogue Items'

    def __str__(self):
        cas = f" (CAS: {self.cas_number})" if self.cas_number else ""
        return f"{self.common_name}{cas}"

    @property
    def is_hazardous(self):
        return bool(self.ghs_hazard_codes)


class NeedsRequest(models.Model):
    """
    A single needs request submitted by a user.
    Multiple requests get consolidated into procurement batches.
    """
    STATUS_CHOICES = [
        ('draft',       'Draft'),
        ('submitted',   'Submitted'),
        ('consolidated','Consolidated'),
        ('approved',    'Approved'),
        ('partial',     'Partially Approved'),
        ('rejected',    'Rejected'),
        ('ordered',     'Ordered'),
        ('received',    'Received'),
    ]

    URGENCY_CHOICES = [
        ('low',    'Low — within 30 days'),
        ('medium', 'Medium — within 14 days'),
        ('high',   'High — within 7 days'),
        ('urgent', 'Urgent — within 3 days'),
    ]

    FLOOR_CHOICES = [
        ('APU', 'APU Building'),
        ('1',   'Floor 1 — Teaching Lab (New Building)'),
        ('2',   'Floor 2 — Teaching Lab (New Building)'),
        ('3',   'Floor 3 — Teaching Lab (New Building)'),
        ('4',   'Floor 4 — Research Lab (New Building)'),
        ('5',   'Floor 5 — Office (New Building)'),
    ]

    PROGRAM_CHOICES = [
        ('Biomedical',  'Biomedical'),
        ('Biotech',     'Biotechnology'),
        ('Agritech',    'Agricultural Technology'),
        ('Food',        'Food Technology'),
        ('Pharmacy',    'Pharmacy'),
        ('Medicine',    'Medicine'),
        ('General',     'General / Cross-program'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_code    = models.CharField(max_length=30, unique=True, editable=False)
    requested_by    = models.ForeignKey(User, on_delete=models.PROTECT, related_name='needs_requests')
    catalogue_item  = models.ForeignKey(CatalogueItem, on_delete=models.PROTECT, related_name='requests')
    quantity_requested = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_approved  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit            = models.CharField(max_length=30)
    reason          = models.TextField(help_text="Why is this item needed?")
    floor           = models.CharField(max_length=3, choices=FLOOR_CHOICES)
    lab_room        = models.CharField(max_length=100, blank=True)
    study_program   = models.CharField(max_length=50, choices=PROGRAM_CHOICES)
    urgency         = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='medium')
    date_needed     = models.DateField()
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    rejection_reason = models.TextField(blank=True)
    reviewed_by     = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_requests'
    )
    reviewed_at     = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Needs Request'
        verbose_name_plural = 'Needs Requests'

    def __str__(self):
        return f"{self.request_code} — {self.catalogue_item.common_name}"

    def save(self, *args, **kwargs):
        if not self.request_code:
            # Generate code: NR-2025-0001
            import datetime
            year = datetime.date.today().year
            last = NeedsRequest.objects.filter(
                request_code__startswith=f'NR-{year}-'
            ).count()
            self.request_code = f'NR-{year}-{str(last + 1).zfill(4)}'
        # Auto-fill unit from catalogue if not set
        if not self.unit and self.catalogue_item:
            self.unit = self.catalogue_item.unit
        super().save(*args, **kwargs)


class ConsolidatedRequest(models.Model):
    """
    Groups multiple NeedsRequests for the same item into one
    procurement line for admin review.
    Auto-created by the consolidation engine.
    """
    STATUS_CHOICES = [
        ('pending',  'Pending Review'),
        ('approved', 'Approved'),
        ('partial',  'Partially Approved'),
        ('rejected', 'Rejected'),
        ('ordered',  'Purchase Order Issued'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    catalogue_item  = models.ForeignKey(CatalogueItem, on_delete=models.PROTECT)
    requests        = models.ManyToManyField(NeedsRequest, related_name='consolidated_in')
    total_quantity  = models.DecimalField(max_digits=10, decimal_places=2)
    approved_quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit            = models.CharField(max_length=30)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes     = models.TextField(blank=True)
    consolidated_at = models.DateTimeField(auto_now_add=True)
    reviewed_by     = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='consolidated_reviews'
    )
    reviewed_at     = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-consolidated_at']
        verbose_name = 'Consolidated Request'
        verbose_name_plural = 'Consolidated Requests'

    def __str__(self):
        return f"Consolidated: {self.catalogue_item.common_name} x{self.total_quantity} {self.unit}"

    @property
    def request_count(self):
        return self.requests.count()
