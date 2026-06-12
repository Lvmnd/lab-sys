"""
serializers.py — Inventory Module
Future University LIMS
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import StockItem, StockMovement, StockAlert
from apps.needs.models import CatalogueItem
from apps.booking.models import LabRoom


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
        fields = ['id', 'item_code', 'common_name', 'category',
                  'unit', 'cas_number', 'ghs_pictograms', 'storage_condition']


class LabRoomBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model  = LabRoom
        fields = ['id', 'room_code', 'name', 'floor', 'floor_display']

    floor_display = serializers.CharField(
        source='get_floor_display', read_only=True
    )


class StockItemSerializer(serializers.ModelSerializer):
    catalogue_item    = CatalogueItemBriefSerializer(read_only=True)
    catalogue_item_id = serializers.UUIDField(write_only=True)
    lab_room          = LabRoomBriefSerializer(read_only=True)
    lab_room_id       = serializers.UUIDField(write_only=True)
    is_low_stock      = serializers.ReadOnlyField()
    is_out_of_stock   = serializers.ReadOnlyField()
    is_expiring_soon  = serializers.ReadOnlyField()
    is_expired        = serializers.ReadOnlyField()
    stock_status      = serializers.SerializerMethodField()

    class Meta:
        model  = StockItem
        fields = [
            'id', 'catalogue_item', 'catalogue_item_id',
            'lab_room', 'lab_room_id',
            'quantity', 'unit', 'min_stock',
            'batch_number', 'expiry_date', 'storage_location',
            'is_low_stock', 'is_out_of_stock',
            'is_expiring_soon', 'is_expired',
            'stock_status', 'last_updated', 'created_at',
        ]
        read_only_fields = ['id', 'last_updated', 'created_at']

    def get_stock_status(self, obj):
        if obj.is_expired:
            return 'expired'
        if obj.is_out_of_stock:
            return 'out_of_stock'
        if obj.is_expiring_soon:
            return 'expiring_soon'
        if obj.is_low_stock:
            return 'low_stock'
        return 'ok'

    def validate(self, data):
        item_id = data.get('catalogue_item_id')
        room_id = data.get('lab_room_id')
        try:
            data['catalogue_item'] = CatalogueItem.objects.get(
                id=item_id, is_active=True
            )
        except CatalogueItem.DoesNotExist:
            raise serializers.ValidationError(
                {"catalogue_item_id": "Catalogue item not found."}
            )
        try:
            data['lab_room'] = LabRoom.objects.get(id=room_id)
        except LabRoom.DoesNotExist:
            raise serializers.ValidationError(
                {"lab_room_id": "Lab room not found."}
            )
        if not data.get('unit'):
            data['unit'] = data['catalogue_item'].unit
        return data

    def create(self, validated_data):
        validated_data.pop('catalogue_item_id', None)
        validated_data.pop('lab_room_id', None)
        return super().create(validated_data)


class StockMovementSerializer(serializers.ModelSerializer):
    stock_item      = StockItemSerializer(read_only=True)
    stock_item_id   = serializers.UUIDField(write_only=True)
    performed_by    = UserBriefSerializer(read_only=True)
    movement_display = serializers.CharField(
        source='get_movement_type_display', read_only=True
    )

    class Meta:
        model  = StockMovement
        fields = [
            'id', 'stock_item', 'stock_item_id',
            'movement_type', 'movement_display',
            'quantity', 'quantity_before', 'quantity_after',
            'reference', 'notes',
            'performed_by', 'created_at',
        ]
        read_only_fields = [
            'id', 'quantity_before', 'quantity_after',
            'performed_by', 'created_at',
        ]

    def validate(self, data):
        item_id = data.get('stock_item_id')
        try:
            data['stock_item'] = StockItem.objects.get(id=item_id)
        except StockItem.DoesNotExist:
            raise serializers.ValidationError(
                {"stock_item_id": "Stock item not found."}
            )
        movement_type = data.get('movement_type')
        quantity      = data.get('quantity', 0)
        stock_item    = data['stock_item']
        if quantity <= 0:
            raise serializers.ValidationError(
                {"quantity": "Quantity must be greater than zero."}
            )
        if movement_type in ('out', 'expired', 'returned'):
            if quantity > stock_item.quantity:
                raise serializers.ValidationError(
                    {"quantity": f"Not enough stock. Available: {stock_item.quantity} {stock_item.unit}"}
                )
        return data

    def create(self, validated_data):
        validated_data.pop('stock_item_id', None)
        stock_item    = validated_data['stock_item']
        movement_type = validated_data['movement_type']
        quantity      = validated_data['quantity']

        validated_data['quantity_before'] = stock_item.quantity
        validated_data['performed_by']    = self.context['request'].user

        if movement_type == 'in':
            stock_item.quantity += quantity
        elif movement_type in ('out', 'expired', 'returned'):
            stock_item.quantity -= quantity
        elif movement_type == 'adjustment':
            stock_item.quantity = quantity

        validated_data['quantity_after'] = stock_item.quantity
        stock_item.save()
        return super().create(validated_data)


class StockAlertSerializer(serializers.ModelSerializer):
    stock_item    = StockItemSerializer(read_only=True)
    resolved_by   = UserBriefSerializer(read_only=True)
    alert_display = serializers.CharField(
        source='get_alert_type_display', read_only=True
    )

    class Meta:
        model  = StockAlert
        fields = [
            'id', 'stock_item', 'alert_type', 'alert_display',
            'message', 'is_resolved',
            'resolved_by', 'resolved_at', 'created_at',
        ]
        read_only_fields = [
            'id', 'resolved_by', 'resolved_at', 'created_at',
        ]


class StockSummarySerializer(serializers.Serializer):
    """Used for the inventory dashboard."""
    total_items       = serializers.IntegerField()
    low_stock_count   = serializers.IntegerField()
    out_of_stock_count = serializers.IntegerField()
    expiring_soon_count = serializers.IntegerField()
    expired_count     = serializers.IntegerField()
    unresolved_alerts = serializers.IntegerField()
