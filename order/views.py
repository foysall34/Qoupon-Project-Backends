from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import (
    Cart, CartItem, CartDeal, Order, OrderItem, 
    AppliedDeal, OrderTracking
)
from .serializers import (
    OrderSerializer, OrderItemSerializer, 
    AppliedDealSerializer, OrderTrackingSerializer
)
from discover.models import MenuItem
from vendors.models import Create_Deal
import json

# Cart Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cart(request):
    """Get user's cart with items and applied deal"""
    cart, _ = Cart.objects.get_or_create(user=request.user)
    data = {
        'id': cart.id,
        'total_items': cart.total_items,
        'subtotal': str(cart.subtotal),
        'delivery_fee': str(cart.delivery_fee),
        'total_discount': str(cart.total_discount),
        'final_total': str(cart.final_total),
        'items': [{
            'id': item.id,
            'menu_item': {
                'id': item.menu_item.id,
                'name': item.menu_item.name,
                'price': str(item.menu_item.price)
            },
            'quantity': item.quantity,
            'special_instructions': item.special_instructions,
            'item_total': str(item.item_total)
        } for item in cart.cart_items.all()],
        'applied_deal': None
    }
    
    if hasattr(cart, 'applied_deal'):
        data['applied_deal'] = {
            'id': cart.applied_deal.deal.id,
            'title': cart.applied_deal.deal.title,
            'discount_amount': str(cart.applied_deal.calculated_discount)
        }
    
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    """Add item to cart or update quantity if already exists"""
    menu_item_id = request.data.get('menu_item_id')
    quantity = int(request.data.get('quantity', 1))
    special_instructions = request.data.get('special_instructions', '')
    
    if quantity < 1:
        return Response(
            {'error': 'Quantity must be positive'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    menu_item = get_object_or_404(MenuItem, id=menu_item_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        menu_item=menu_item,
        defaults={
            'quantity': quantity,
            'special_instructions': special_instructions
        }
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.special_instructions = special_instructions
        cart_item.save()
    
    return Response({
        'message': 'Item added to cart',
        'cart_total': str(cart.final_total)
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    """Update cart item quantity or special instructions"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = request.data.get('quantity')
    special_instructions = request.data.get('special_instructions')
    
    if quantity is not None:
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    
    if special_instructions is not None:
        cart_item.special_instructions = special_instructions
        cart_item.save()
    
    return Response({'message': 'Cart updated'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    """Clear all items from cart"""
    cart = get_object_or_404(Cart, user=request.user)
    cart.clear()
    return Response({'message': 'Cart cleared'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_checkout(request):
    """Calculate final order amount with deal if provided"""
    cart = get_object_or_404(Cart, user=request.user)
    deal_id = request.data.get('deal_id')
    
    checkout_data = {
        'subtotal': str(cart.subtotal),
        'delivery_fee': str(cart.delivery_fee),
        'discount_amount': '0.00',
        'final_total': str(cart.final_total)
    }
    
    if deal_id:
        deal = get_object_or_404(Create_Deal, id=deal_id)
        # Calculate discount
        if deal.discount_value <= 100:  # Percentage discount
            discount = (cart.subtotal * Decimal(str(deal.discount_value))) / Decimal('100.00')
        else:  # Fixed amount discount
            discount = min(Decimal(str(deal.discount_value)), cart.subtotal)
        
        checkout_data.update({
            'discount_amount': str(discount),
            'final_total': str(cart.final_total - discount),
            'applied_deal': {
                'id': deal.id,
                'title': deal.title
            }
        })
    
    return Response(checkout_data)

# Order Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_list(request):
    """Get list of user's orders"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, order_id):
    """Get detailed information about an order"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    serializer = OrderSerializer(order)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def create_order(request):
    """Create a new order from cart with initial PENDING_PAYMENT status"""
    cart = get_object_or_404(Cart, user=request.user)
    deal_id = request.data.get('deal_id')
    
    if not cart.cart_items.exists():
        return Response(
            {'error': 'Cannot create order with empty cart'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calculate totals including deal if provided
    subtotal = cart.subtotal
    delivery_fee = cart.delivery_fee
    discount_amount = Decimal('0.00')
    
    if deal_id:
        deal = get_object_or_404(Create_Deal, id=deal_id)
        if deal.discount_value <= 100:  # Percentage discount
            discount_amount = (subtotal * Decimal(str(deal.discount_value))) / Decimal('100.00')
        else:  # Fixed amount discount
            discount_amount = min(Decimal(str(deal.discount_value)), subtotal)
    
    total_amount = subtotal + delivery_fee - discount_amount
    
    # Create cart snapshot
    cart_data = {
        'items': [{
            'menu_item_id': item.menu_item.id,
            'name': item.menu_item.name,
            'quantity': item.quantity,
            'unit_price': str(item.unit_price),
            'total': str(item.item_total),
            'special_instructions': item.special_instructions
        } for item in cart.cart_items.all()],
        'subtotal': str(subtotal),
        'delivery_fee': str(delivery_fee),
        'discount': str(discount_amount),
        'final_total': str(total_amount)
    }
    
    if deal_id:
        cart_data['applied_deal'] = {
            'deal_id': deal.id,
            'title': deal.title,
            'discount_amount': str(discount_amount)
        }
    
    # Create order with PENDING_PAYMENT status
    order = Order.objects.create(
        user=request.user,
        cart_snapshot=cart_data,
        delivery_type=request.data.get('delivery_type'),
        order_type=request.data.get('order_type'),
        scheduled_datetime=request.data.get('scheduled_datetime'),
        delivery_address=request.data.get('delivery_address'),
        delivery_postal_code=request.data.get('delivery_postal_code'),
        special_instructions=request.data.get('special_instructions'),
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        discount_amount=discount_amount,
        total_amount=total_amount,
        status=Order.OrderStatus.PENDING_PAYMENT
    )
    
    # Create order items
    for cart_item in cart.cart_items.all():
        OrderItem.objects.create(
            order=order,
            menu_item=cart_item.menu_item,
            quantity=cart_item.quantity,
            unit_price=cart_item.unit_price,
            total_price=cart_item.item_total,
            item_name=cart_item.menu_item.name,
            item_description=cart_item.menu_item.description,
            special_instructions=cart_item.special_instructions
        )
    
    # Create applied deal if exists
    if deal_id:
        AppliedDeal.objects.create(
            order=order,
            deal=deal,
            discount_amount=discount_amount,
            deal_title=deal.title,
            deal_description=deal.description
        )
    
    # Create initial tracking
    OrderTracking.objects.create(
        order=order,
        status=Order.OrderStatus.PENDING_PAYMENT,
        note='Order created, awaiting payment'
    )
    
    serializer = OrderSerializer(order)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_payment(request, order_id):
    """Process payment and update order status to RECEIVED if successful"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    if order.status != Order.OrderStatus.PENDING_PAYMENT:
        return Response(
            {'error': 'Order is not in pending payment state'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Here you would integrate with your payment gateway
    # For now, we'll simulate a successful payment
    payment_successful = True  # This would come from payment gateway
    
    if payment_successful:
        order.status = Order.OrderStatus.RECEIVED
        order.payment_status = Order.PaymentStatus.PAID
        order.save()
        
        # Create tracking entry
        OrderTracking.objects.create(
            order=order,
            status=Order.OrderStatus.RECEIVED,
            note='Payment successful, order received'
        )
        
        # Clear the cart after successful payment
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart.clear()
        
        return Response({
            'message': 'Payment successful, order received',
            'order': OrderSerializer(order).data
        })
    else:
        return Response(
            {'error': 'Payment failed'},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_order(request, order_id):
    """Cancel an order"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    if order.status in [Order.OrderStatus.COMPLETED, Order.OrderStatus.CANCELLED]:
        return Response(
            {'error': 'Cannot cancel completed or already cancelled orders'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    order.status = Order.OrderStatus.CANCELLED
    order.save()
    
    OrderTracking.objects.create(
        order=order,
        status=Order.OrderStatus.CANCELLED,
        note=request.data.get('cancellation_reason', 'Order cancelled by user')
    )
    
    return Response({'message': 'Order cancelled successfully'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_tracking(request, order_id):
    """Get order tracking history"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    tracking = order.tracking_history.all()
    serializer = OrderTrackingSerializer(tracking, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_delivery_qr(request, order_id):
    """Get delivery QR code for an order"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    if order.status not in [Order.OrderStatus.PREPARING, Order.OrderStatus.OUT_FOR_DELIVERY]:
        return Response(
            {'error': 'QR code is only available for orders in preparation or out for delivery'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not order.delivery_code:
        return Response(
            {'error': 'Delivery code not generated yet'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response({
        'delivery_code': order.delivery_code,
        'qr_data': order.delivery_code,
        'created_at': order.delivery_code_created_at
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_delivery(request, order_id):
    """Verify delivery using QR code"""
    order = get_object_or_404(Order, order_id=order_id)
    delivery_code = request.data.get('delivery_code')
    
    if not delivery_code:
        return Response(
            {'error': 'Delivery code is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if order.status not in [Order.OrderStatus.OUT_FOR_DELIVERY, Order.OrderStatus.READY_FOR_PICKUP]:
        return Response(
            {'error': 'Order is not ready for delivery verification'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if order.delivery_code_used:
        return Response(
            {'error': 'Delivery code has already been used'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if order.delivery_code != delivery_code:
        return Response(
            {'error': 'Invalid delivery code'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Mark delivery as verified
    order.delivery_code_used = True
    order.status = Order.OrderStatus.COMPLETED
    order.save()
    
    # Create tracking entry
    OrderTracking.objects.create(
        order=order,
        status=Order.OrderStatus.COMPLETED,
        note='Delivery verified via QR code'
    )
    
    return Response({
        'message': 'Delivery verified successfully',
        'order_status': order.status
    })
