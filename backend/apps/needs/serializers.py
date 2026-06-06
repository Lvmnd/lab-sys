"""
serializers.py — Needs Request Module
Future University LIMS
Converts models to/from JSON for the REST API
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CatalogueItem, NeedsRequest, ConsolidatedRequest
import datetime


class CatalogueItemSerializer(serializers.ModelSerializer):
    is_hazardous = serializers.ReadOnlyField()

    class Meta:
        model  = CatalogueItem
        fields = [
            'id', 'item_code', 'common_name', 'iupac_name',
            'cas_number', 'molecular_formula', 'molecular_weight',
            'category', 'unit', 'ghs_hazard_codes', 'ghs_pictograms',
            'storage_condition', 'study_programs', 'is_hazardous', 'is_active',
        ]


class CatalogueItemSearchSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for search dropdown in the needs request form.
    Returns only what the frontend needs to show suggestions.
    """
    display_label = serializers.SerializerMethodField()

    class Meta:
        model  = CatalogueItem
        fields = [
            'id', 'item_code', 'common_name', 'iupac_name',
            'cas_number', 'category', 'unit',
            'ghs_hazard_codes', 'ghs_pictograms',
            'storage_condition', 'is_hazardous', 'display_label',
        ]

    def get_display_label(self, obj):
        cas = f" — CAS: {obj.cas_number}" if obj.cas_number else ""
        return f"{obj.common_name}{cas} [{obj.category}]"


class UserBriefSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ['id', 'username', 'full_name', 'email']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class NeedsRequestSerializer(serializers.ModelSerializer):
    requested_by    = UserBriefSerializer(read_only=True)
    reviewed_by     = UserBriefSerializer(read_only=True)
    catalogue_item  = CatalogueItemSerializer(read_only=True)
    catalogue_item_id = serializers.UUIDField(write_only=True)
    status_display  = serializers.CharField(source='get_status_display', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    floor_display   = serializers.CharField(source='get_floor_display', read_only=True)
    program_display = serializers.CharField(source='get_study_program_display', read_only=True)
    is_overdue      = serializers.SerializerMethodField()

    class Meta:
        model  = NeedsRequest
        fields = [
            'id', 'request_code',
            'requested_by', 'reviewed_by',
            'catalogue_item', 'catalogue_item_id',
            'quantity_requested', 'quantity_approved', 'unit',
            'reason', 'floor', 'floor_display',
            'lab_room', 'study_program', 'program_display',
            'urgency', 'urgency_display',
            'date_needed', 'status', 'status_display',
            'rejection_reason',
            'reviewed_at', 'created_at', 'updated_at',
            'is_overdue',
        ]
        read_only_fields = [
            'id', 'request_code', 'requested_by',
            'quantity_approved', 'rejection_reason',
            'reviewed_by', 'reviewed_at',
            'created_at', 'updated_at',
        ]

    def get_is_overdue(self, obj):
        if obj.status in ('received', 'rejected'):
            return False
        return obj.date_needed < datetime.date.today()

    def validate_date_needed(self, value):
        if value < datetime.date.today():
            raise serializers.ValidationError("Date needed cannot be in the past.")
        return value

    def validate_quantity_requested(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate(self, data):
        # Ensure catalogue item exists and is active
        item_id = data.get('catalogue_item_id')
        if item_id:
            try:
                item = CatalogueItem.objects.get(id=item_id, is_active=True)
                data['catalogue_item'] = item
                # Auto-fill unit from catalogue
                if not data.get('unit'):
                    data['unit'] = item.unit
            except CatalogueItem.DoesNotExist:
                raise serializers.ValidationError(
                    {"catalogue_item_id": "Item not found in catalogue or is inactive."}
                )
        return data

    def create(self, validated_data):
        validated_data.pop('catalogue_item_id', None)
        validated_data['requested_by'] = self.context['request'].user
        validated_data['status'] = 'submitted'
        return super().create(validated_data)


class NeedsRequestApprovalSerializer(serializers.Serializer):
    """Used by admin to approve or reject a consolidated request."""
    action            = serializers.ChoiceField(choices=['approve', 'partial', 'reject'])
    approved_quantity = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        required=False, allow_null=True
    )
    admin_notes       = serializers.CharField(required=False, allow_blank=True)
    rejection_reason  = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        action = data.get('action')
        if action == 'partial' and not data.get('approved_quantity'):
            raise serializers.ValidationError(
                {"approved_quantity": "Approved quantity is required for partial approval."}
            )
        if action == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError(
                {"rejection_reason": "Rejection reason is required."}
            )
        return data


class ConsolidatedRequestSerializer(serializers.ModelSerializer):
    catalogue_item  = CatalogueItemSerializer(read_only=True)
    reviewed_by     = UserBriefSerializer(read_only=True)
    requests        = NeedsRequestSerializer(many=True, read_only=True)
    request_count   = serializers.ReadOnlyField()
    status_display  = serializers.CharField(source='get_status_display', read_only=True)
    requesters      = serializers.SerializerMethodField()
    programs        = serializers.SerializerMethodField()

    class Meta:
        model  = ConsolidatedRequest
        fields = [
            'id', 'catalogue_item',
            'total_quantity', 'approved_quantity', 'unit',
            'status', 'status_display',
            'request_count', 'requests',
            'requesters', 'programs',
            'admin_notes', 'reviewed_by', 'reviewed_at',
            'consolidated_at',
        ]

    def get_requesters(self, obj):
        """List of unique users who requested this item."""
        users = obj.requests.values_list(
            'requested_by__username',
            'requested_by__first_name',
            'requested_by__last_name'
        ).distinct()
        return [
            u[1] + ' ' + u[2] if (u[1] or u[2]) else u[0]
            for u in users
        ]

    def get_programs(self, obj):
        """List of unique study programs requesting this item."""
        return list(
            obj.requests.values_list('study_program', flat=True).distinct()
        )
