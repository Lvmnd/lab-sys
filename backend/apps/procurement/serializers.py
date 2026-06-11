"""
serializers.py — Procurement Module
Future University LIMS
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import PurchaseOrder, POLineItem, GoodsReceipt, GoodsReceiptItem
from apps.needs.models import CatalogueItem, ConsolidatedRequest
import datetime


class UserBriefSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ['id', 'username', 'full_name']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class CatalogueItemBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CatalogueItem
        fields = ['id', 'item_code', 'common_name', 'category', 'unit',
                  'cas_number', 'storage_condition']


class POLineItemSerializer(serializers.ModelSerializer):
    catalogue_item       = CatalogueItemBriefSerializer(read_only=True)
    catalogue_item_id    = serializers.UUIDField(write_only=True)
    consolidated_request_id = serializers.UUIDField(
        write_only=True, required=False, allow_null=True
    )
    total_price          = serializers.ReadOnlyField()
    is_fully_received    = serializers.ReadOnlyField()
    status_display       = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model  = POLineItem
        fields = [
            'id', 'catalogue_item', 'catalogue_item_id',
            'consolidated_request_id',
            'quantity_ordered', 'quantity_received', 'unit',
            'unit_price', 'total_price',
            'status', 'status_display',
            'is_fully_received', 'notes',
        ]
        read_only_fields = ['id', 'quantity_received']

    def validate(self, data):
        item_id = data.get('catalogue_item_id')
        try:
            item = CatalogueItem.objects.get(id=item_id, is_active=True)
            data['catalogue_item'] = item
            if not data.get('unit'):
                data['unit'] = item.unit
        except CatalogueItem.DoesNotExist:
            raise serializers.ValidationError(
                {"catalogue_item_id": "Item not found in catalogue."}
            )
        cr_id = data.get('consolidated_request_id')
        if cr_id:
            try:
                data['consolidated_request'] = ConsolidatedRequest.objects.get(id=cr_id)
            except ConsolidatedRequest.DoesNotExist:
                raise serializers.ValidationError(
                    {"consolidated_request_id": "Consolidated request not found."}
                )
        return data

    def create(self, validated_data):
        validated_data.pop('catalogue_item_id', None)
        validated_data.pop('consolidated_request_id', None)
        return super().create(validated_data)


class PurchaseOrderSerializer(serializers.ModelSerializer):
    created_by      = UserBriefSerializer(read_only=True)
    approved_by     = UserBriefSerializer(read_only=True)
    line_items      = POLineItemSerializer(many=True, read_only=True)
    line_item_count = serializers.SerializerMethodField()
    status_display  = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model  = PurchaseOrder
        fields = [
            'id', 'po_number', 'title', 'status', 'status_display',
            'supplier', 'notes', 'total_amount',
            'created_by', 'approved_by', 'approved_at',
            'expected_delivery',
            'line_items', 'line_item_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'po_number', 'created_by',
            'approved_by', 'approved_at',
            'total_amount', 'created_at', 'updated_at',
        ]

    def get_line_item_count(self, obj):
        return obj.line_items.count()

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class PurchaseOrderBriefSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    line_item_count = serializers.SerializerMethodField()

    class Meta:
        model  = PurchaseOrder
        fields = [
            'id', 'po_number', 'title', 'status', 'status_display',
            'supplier', 'total_amount', 'line_item_count',
            'expected_delivery', 'created_at',
        ]

    def get_line_item_count(self, obj):
        return obj.line_items.count()


class GoodsReceiptItemSerializer(serializers.ModelSerializer):
    po_line_item_id  = serializers.UUIDField(write_only=True)
    item_name        = serializers.CharField(
        source='po_line_item.catalogue_item.common_name', read_only=True
    )
    item_code        = serializers.CharField(
        source='po_line_item.catalogue_item.item_code', read_only=True
    )
    unit             = serializers.CharField(
        source='po_line_item.unit', read_only=True
    )
    quantity_ordered = serializers.DecimalField(
        source='po_line_item.quantity_ordered',
        max_digits=10, decimal_places=2, read_only=True
    )
    condition_display = serializers.CharField(
        source='get_condition_display', read_only=True
    )

    class Meta:
        model  = GoodsReceiptItem
        fields = [
            'id', 'po_line_item_id',
            'item_name', 'item_code',
            'quantity_ordered', 'quantity_received', 'unit',
            'batch_number', 'expiry_date',
            'storage_location', 'condition', 'condition_display',
            'notes',
        ]
        read_only_fields = ['id']

    def validate(self, data):
        line_id = data.get('po_line_item_id')
        try:
            line = POLineItem.objects.get(id=line_id)
            data['po_line_item'] = line
        except POLineItem.DoesNotExist:
            raise serializers.ValidationError(
                {"po_line_item_id": "PO line item not found."}
            )
        qty = data.get('quantity_received', 0)
        if qty <= 0:
            raise serializers.ValidationError(
                {"quantity_received": "Received quantity must be greater than zero."}
            )
        return data

    def create(self, validated_data):
        validated_data.pop('po_line_item_id', None)
        return super().create(validated_data)


class GoodsReceiptSerializer(serializers.ModelSerializer):
    received_by    = UserBriefSerializer(read_only=True)
    purchase_order = PurchaseOrderBriefSerializer(read_only=True)
    purchase_order_id = serializers.UUIDField(write_only=True)
    items          = GoodsReceiptItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model  = GoodsReceipt
        fields = [
            'id', 'receipt_number',
            'purchase_order', 'purchase_order_id',
            'status', 'status_display',
            'received_by', 'received_date',
            'supplier_invoice', 'notes',
            'items', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'receipt_number', 'received_by',
            'created_at', 'updated_at',
        ]

    def validate(self, data):
        po_id = data.get('purchase_order_id')
        try:
            po = PurchaseOrder.objects.get(id=po_id)
            if po.status not in ('approved', 'ordered', 'partial'):
                raise serializers.ValidationError(
                    {"purchase_order_id":
                     f"Cannot receive goods for a PO with status '{po.status}'."}
                )
            data['purchase_order'] = po
        except PurchaseOrder.DoesNotExist:
            raise serializers.ValidationError(
                {"purchase_order_id": "Purchase order not found."}
            )
        return data

    def create(self, validated_data):
        validated_data.pop('purchase_order_id', None)
        validated_data['received_by'] = self.context['request'].user
        if not validated_data.get('received_date'):
            import datetime
            validated_data['received_date'] = datetime.date.today()
        return super().create(validated_data)
