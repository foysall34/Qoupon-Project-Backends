from rest_framework import serializers
from .models import Order, OrderItem, AppliedDeal, OrderTracking
from discover.models import Cart, CartItem
from django.utils import timezone
from datetime import timedelta

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'quantity', 'unit_price', 'total_price', 
                 'item_name', 'item_description', 'special_instructions']
        read_only_fields = ['unit_price', 'total_price', 'item_name', 'item_description']

class AppliedDealSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppliedDeal
        fields = ['id', 'deal', 'discount_amount', 'deal_title', 'deal_description']
        read_only_fields = ['deal_title', 'deal_description']

class OrderTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderTracking
        fields = ['id', 'status', 'timestamp', 'note']
        read_only_fields = ['timestamp']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    applied_deals = AppliedDealSerializer(many=True, read_only=True)
    tracking_history = OrderTrackingSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'user', 'cart', 'status', 'payment_status',
            'delivery_type', 'order_type', 'scheduled_datetime',
            'subtotal', 'delivery_fee', 'discount_amount', 'total_amount',
            'delivery_address', 'delivery_postal_code', 'special_instructions',
            'estimated_delivery_time', 'items', 'applied_deals', 'tracking_history',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'order_id', 'subtotal', 'total_amount', 'created_at', 'updated_at',
            'estimated_delivery_time'
        ]

    def validate_scheduled_datetime(self, value):
        """
        Validate scheduled datetime:
        - Required if order_type is SCHEDULED
        - Must be in the future
        - Must be at least 1 hour in the future
        """
        if self.initial_data.get('order_type') == Order.OrderType.SCHEDULED:
            if not value:
                raise serializers.ValidationError(
                    "Scheduled datetime is required for scheduled orders.")
            
            min_time = timezone.now() + timedelta(hours=1)
            if value < min_time:
                raise serializers.ValidationError(
                    "Scheduled time must be at least 1 hour in the future.")
        return value

    def validate(self, data):
        """
        Additional validation:
        - Delivery address and postal code required for delivery orders
        - Cart must exist and have items
        """
        if data.get('delivery_type') == Order.DeliveryType.DELIVERY:
            if not data.get('delivery_address'):
                raise serializers.ValidationError(
                    {"delivery_address": "Delivery address is required for delivery orders."})
            if not data.get('delivery_postal_code'):
                raise serializers.ValidationError(
                    {"delivery_postal_code": "Postal code is required for delivery orders."})

        cart = data.get('cart')
        if not cart:
            raise serializers.ValidationError({"cart": "Cart is required."})
        if not cart.items.exists():
            raise serializers.ValidationError({"cart": "Cart is empty."})

        return data

    def create(self, validated_data):
        cart = validated_data['cart']
        order = Order.objects.create(**validated_data)

        # Create OrderItems from CartItems
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                menu_item=cart_item.menu_item,
                quantity=cart_item.quantity,
                special_instructions=''  # Can be added in the future if needed
            )

        # Create initial tracking entry
        OrderTracking.objects.create(
            order=order,
            status=Order.OrderStatus.RECEIVED,
            note='Order received'
        )

        return order