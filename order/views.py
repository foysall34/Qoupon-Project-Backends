from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.conf import settings
from decimal import Decimal
import logging
from mollie.api.client import Client
from mollie.api.error import UnprocessableEntityError, Error as MollieApiError
 
logger = logging.getLogger(__name__)
from .models import (
    Cart, CartItem, CartDeal, Order, OrderItem,
    AppliedDeal, OrderTracking
)
from .serializers import (
    OrderSerializer, OrderItemSerializer,
    AppliedDealSerializer, OrderTrackingSerializer
)
from vendors.models import Deal, Create_Deal, Business_profile
from rest_framework.exceptions import PermissionDenied
import json
 
# Cart Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cart(request):
    """Get user's cart with items and applied deal"""
    cart, _ = Cart.objects.get_or_create(user=request.user)
    # Calculate discount if a deal is applied
    applied_discount = Decimal('0.00')
    if hasattr(cart, 'applied_deal'):
        applied_discount = cart.applied_deal.calculated_discount
 
    data = {
        'id': cart.id,
        'total_items': cart.total_items,
        'subtotal': str(cart.subtotal),
        'delivery_fee': str(cart.delivery_fee),
        'total_discount': str(applied_discount),
        'final_total': str(cart.final_total),
        'items': [{
            'id': item.id,
            'deal': {
                'id': item.deal.id,
                'title': item.deal.title,
                'description': item.deal.description,
                'price': str(item.deal.price),
                'image': item.deal.image.url if item.deal.image else None
            },
            'quantity': item.quantity,
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
    """Add deal to cart or update quantity if already exists"""
    deal_id = request.data.get('menu_item_id')
    quantity = int(request.data.get('quantity', 1))
    
    if quantity < 1:
        return Response(
            {'error': 'Quantity must be positive'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    deal = get_object_or_404(Deal, id=deal_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        deal=deal,
        defaults={
            'quantity': quantity
        }
    )
    return Response({'message': 'Item added to cart','cart_total':str(cart.final_total)}, status=status.HTTP_201_CREATED)
 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = request.data.get('quantity')
    
    if quantity is not None:
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    
    return Response({'message': 'Cart updated'})
 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    """Clear all items from cart"""
    cart = get_object_or_404(Cart, user=request.user)
    cart.clear()
    return Response({'message': 'Cart cleared'})
  
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_cart_item(request, item_id):
    """Delete specific item from cart"""
    print(item_id)
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return Response({'message': 'Item removed from cart'}, status=status.HTTP_200_OK)
 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def increment_cart_item(request, item_id):
    """Increase quantity of cart item by 1"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.quantity += 1
    cart_item.save()
    return Response({
        'message': 'Quantity increased',
        'quantity': cart_item.quantity,
        'item_total': str(cart_item.item_total),
        'cart_total': str(cart_item.cart.final_total)
    })
 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def decrement_cart_item(request, item_id):
    """Decrease quantity of cart item by 1"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
        message = 'Quantity decreased'
    else:
        cart_item.delete()
        message = 'Item removed from cart'
    
    cart = Cart.objects.get(user=request.user)
    return Response({
        'message': message,
        'quantity': cart_item.quantity if cart_item.quantity > 1 else 0,
        'item_total': str(cart_item.item_total) if cart_item.quantity > 1 else "0.00",
        'cart_total': str(cart.final_total)
    })
 
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
            'deal_id': item.deal.id,
            'title': item.deal.title,
            'quantity': item.quantity,
            'unit_price': str(item.unit_price),
            'total': str(item.item_total)
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
        note=request.data.get('note', ''),
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
            menu_item=cart_item.deal,
            quantity=cart_item.quantity,
            unit_price=cart_item.deal.price,
            total_price=cart_item.item_total,
            item_name=cart_item.deal.title,
            item_description=cart_item.deal.description
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
    """Process payment using Mollie payment gateway"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    if order.status != Order.OrderStatus.PENDING_PAYMENT:
        return Response(
            {'error': 'Order is not in pending payment state'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        mollie_client = Client()
        mollie_client.set_api_key(settings.MOLLIE_API_KEY)
    except Exception as e:
        logger.error(f"Mollie API initialization error: {e}")
        return Response(
            {'error': 'Payment service unavailable'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
 
    try:
        payment_data = {
            'amount': {
                'currency': 'EUR',
                'value': f"{float(order.total_amount):.2f}"
            },
            'description': f'Order #{order.order_id}',
            'redirectUrl': f'{settings.FRONTEND_URL}/orders/{order.order_id}/confirmation/',
            'webhookUrl': f'{settings.BACKEND_URL}/api/orders/mollie-webhook/',
            'metadata': {
                'order_id': str(order.order_id)
            }
        }
 
        payment = mollie_client.payments.create(payment_data)
        
        # Store payment ID in order for webhook processing
        order.payment_id = payment.id
        order.save()
        
        return Response({
            'checkout_url': payment.checkout_url
        }, status=status.HTTP_201_CREATED)
 
    except UnprocessableEntityError as e:
        logger.error(f"Mollie payment creation error: {e}")
        return Response(
            {'error': f'Invalid payment data: {e.detail}'},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    except MollieApiError as e:
        logger.error(f"Mollie API error: {e}")
        return Response(
            {'error': 'Payment service error'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        logger.error(f"Unexpected error in payment processing: {e}")
        return Response(
            {'error': 'An unexpected error occurred'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
    
    if order.status == Order.OrderStatus.CANCELLED:
        return Response(
            {'error': 'QR code is not available for cancelled orders'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if order.delivery_code_used:
        return Response(
            {'error': 'QR code has already been used'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not order.qr_code:
        return Response(
            {'error': 'QR code not generated yet'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response({
        'delivery_code': order.delivery_code,
        'qr_code_url': order.qr_code.image.url if order.qr_code else None
    })
 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@api_view(['POST'])
@permission_classes([])  # No authentication required for webhook
def mollie_webhook(request):
    """Handle Mollie payment status webhook"""
    payment_id = request.POST.get('id')
    if not payment_id:
        return Response({'error': 'No payment ID provided'}, status=status.HTTP_400_BAD_REQUEST)
 
    try:
        mollie_client = Client()
        mollie_client.set_api_key(settings.MOLLIE_API_KEY)
        payment = mollie_client.payments.get(payment_id)
        
        # Find the order associated with this payment
        order = Order.objects.filter(payment_id=payment_id).first()
        if not order:
            logger.error(f"Order not found for payment {payment_id}")
            return Response(status=status.HTTP_200_OK)  # Always return 200 to Mollie
        
        if payment.is_paid():
            # Payment was successful
            order.status = Order.OrderStatus.RECEIVED
            order.payment_status = Order.PaymentStatus.PAID
            order.save()
            
            # Create tracking entry
            OrderTracking.objects.create(
                order=order,
                status=Order.OrderStatus.RECEIVED,
                note='Payment successful, order received'
            )
            
            # Clear the user's cart
            Cart.objects.filter(user=order.user).first().clear()
            
        elif payment.is_canceled():
            order.status = Order.OrderStatus.CANCELLED
            order.payment_status = Order.PaymentStatus.CANCELLED
            order.save()
            
            OrderTracking.objects.create(
                order=order,
                status=Order.OrderStatus.CANCELLED,
                note='Payment was cancelled'
            )
            
        elif payment.is_expired():
            order.status = Order.OrderStatus.CANCELLED
            order.payment_status = Order.PaymentStatus.FAILED
            order.save()
            
            OrderTracking.objects.create(
                order=order,
                status=Order.OrderStatus.CANCELLED,
                note='Payment expired'
            )
            
        elif payment.is_failed():
            order.status = Order.OrderStatus.CANCELLED
            order.payment_status = Order.PaymentStatus.FAILED
            order.save()
            
            OrderTracking.objects.create(
                order=order,
                status=Order.OrderStatus.CANCELLED,
                note='Payment failed'
            )
        
        return Response(status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error processing Mollie webhook: {e}")
        return Response(status=status.HTTP_200_OK)  # Always return 200 to Mollie
 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_order_status(request, order_id):
    """Update order status - Only vendors can update their own order statuses"""
    
    # Check if user is a vendor (has a business profile)
    try:
        vendor_profile = Business_profile.objects.get(owner=request.user)
    except Business_profile.DoesNotExist:
        raise PermissionDenied("Only vendors can update order status")
    
    # Get the order
    order = get_object_or_404(Order, order_id=order_id)
    
    # Check if any items in the order belong to this vendor
    vendor_items = order.items.filter(deal__user=request.user)
    if not vendor_items.exists():
        raise PermissionDenied("You can only update orders for your own deals")
    
    new_status = request.data.get('status')
    if not new_status:
        return Response(
            {'error': 'Status is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if new_status not in dict(Order.OrderStatus.choices):
        return Response(
            {'error': 'Invalid status'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Only allow specific status changes for vendors
    allowed_transitions = {
        Order.OrderStatus.RECEIVED: [Order.OrderStatus.PREPARING],
        Order.OrderStatus.PREPARING: [Order.OrderStatus.READY_FOR_PICKUP, Order.OrderStatus.OUT_FOR_DELIVERY]
    }
    
    if order.status not in allowed_transitions or new_status not in allowed_transitions[order.status]:
        return Response(
            {'error': f'Vendors can only change status:\n'
                     f'- From RECEIVED to PREPARING\n'
                     f'- From PREPARING to READY_FOR_PICKUP or OUT_FOR_DELIVERY\n'
                     f'- Order completion requires QR code verification'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # For READY_FOR_PICKUP/OUT_FOR_DELIVERY, validate based on delivery type
    if new_status in [Order.OrderStatus.READY_FOR_PICKUP, Order.OrderStatus.OUT_FOR_DELIVERY]:
        if new_status == Order.OrderStatus.READY_FOR_PICKUP and order.delivery_type != Order.DeliveryType.PICKUP:
            return Response(
                {'error': 'Cannot set to READY_FOR_PICKUP for delivery orders'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if new_status == Order.OrderStatus.OUT_FOR_DELIVERY and order.delivery_type != Order.DeliveryType.DELIVERY:
            return Response(
                {'error': 'Cannot set to OUT_FOR_DELIVERY for pickup orders'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    if order.status in valid_transitions and new_status not in valid_transitions[order.status]:
        return Response(
            {'error': f'Cannot change status from {order.status} to {new_status}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    order.status = new_status
    order.save()
    
    # Create tracking entry
    OrderTracking.objects.create(
        order=order,
        status=new_status,
        note=request.data.get('note', f'Order status updated to {new_status} by {vendor_profile.name}')
    )
    
    return Response({
        'message': 'Order status updated successfully',
        'status': new_status
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_delivery(request, order_id):
    """Verify delivery using QR code - This is the only way to complete an order"""
    order = get_object_or_404(Order, order_id=order_id)
    delivery_code = request.data.get('delivery_code')
    
    if not delivery_code:
        return Response(
            {'error': 'Delivery code is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if order.status == Order.OrderStatus.CANCELLED:
        return Response(
            {'error': 'Cannot verify delivery for cancelled orders'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if order.status not in [Order.OrderStatus.OUT_FOR_DELIVERY, Order.OrderStatus.READY_FOR_PICKUP]:
        return Response(
            {'error': 'Order must be in OUT_FOR_DELIVERY or READY_FOR_PICKUP status for verification'},
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
    
    # Mark delivery as verified and complete the order
    order.delivery_code_used = True
    order.status = Order.OrderStatus.COMPLETED
    order.save()
    
    # Create tracking entry
    OrderTracking.objects.create(
        order=order,
        status=Order.OrderStatus.COMPLETED,
        note='Order completed - verified via QR code'
    )
    
    return Response({
        'message': 'Delivery verified and order completed successfully',
        'order_status': order.status
    })