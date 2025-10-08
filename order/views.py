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
from notifications.utils import FirebaseNotification
import json
from subscription.models import Subscription
 
# Cart Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cart(request):
    """Get user's cart with items and applied deal"""
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    # Get all required modifiers for items in cart that are missing selections
    missing_required_modifiers = []
    for item in cart.cart_items.all():
        deal_modifiers = item.deal.modifiers
        required_groups = [group for group in deal_modifiers if group['is_required']]
        selected_groups = {mod['group_name'] for mod in item.selected_modifiers}
        
        for group in required_groups:
            if group['name'] not in selected_groups:
                missing_required_modifiers.append({
                    'cart_item_id': item.id,
                    'deal_name': item.deal.title,
                    'group_name': group['name'],
                    'available_options': [opt['title'] for opt in group['options']]
                })
    
    # Calculate discount if a deal is applied
    applied_discount = Decimal('0.00')
    if hasattr(cart, 'applied_deal'):
        applied_discount = cart.applied_deal.calculated_discount
        
    if missing_required_modifiers:
        return Response({
            'error': 'Missing required selections',
            'missing_modifiers': missing_required_modifiers
        }, status=status.HTTP_400_BAD_REQUEST)
 
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
            'modifier_groups': [{
                'name': modifier_group['name'],
                'is_required': modifier_group['is_required'],
                'selections': [
                    {
                        'title': option['title'],
                        'price': str(option.get('Price', '0.00'))
                    }
                    for option in modifier_group['options']
                    if any(selection == option['title'] 
                          for selection in next((s['selected_options'] 
                                               for s in item.selected_modifiers 
                                               if s['group_name'] == modifier_group['name']), 
                                              []))
                ]
            } for modifier_group in item.deal.modifiers],
            'base_price': str(item.deal.price),
            'modifiers_price': str(item.modifiers_price),
            'unit_price': str(item.unit_price),
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
    selected_modifiers = request.data.get('selected_modifiers', [])
    
    if quantity < 1:
        return Response(
            {'error': 'Quantity must be positive'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    deal = get_object_or_404(Deal, id=deal_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    # Format the selected modifiers if they're not in the correct format
    if selected_modifiers and not isinstance(selected_modifiers, list):
        return Response(
            {'error': 'selected_modifiers must be a list of selections'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate required modifiers
    required_groups = [group['name'] for group in deal.modifiers if group['is_required']]
    selected_groups = [mod['group_name'] for mod in selected_modifiers]
    missing_required = set(required_groups) - set(selected_groups)
    
    if missing_required:
        return Response(
            {'error': f'Required modifier groups missing: {", ".join(missing_required)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate selections against available options
    for selection in selected_modifiers:
        group_name = selection['group_name']
        selected_options = selection['selected_options']
        
        # Find the corresponding modifier group
        modifier_group = next((group for group in deal.modifiers if group['name'] == group_name), None)
        if not modifier_group:
            return Response(
                {'error': f'Invalid modifier group: {group_name}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate selected options
        available_options = [option['title'] for option in modifier_group['options']]
        invalid_options = set(selected_options) - set(available_options)
        if invalid_options:
            return Response(
                {'error': f'Invalid options for {group_name}: {", ".join(invalid_options)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Create or update cart item
    # Show required modifiers if none provided and modifiers exist
    if not selected_modifiers and deal.modifiers:
        # Only return required modifiers response if there are modifiers defined
        required_modifiers = [
            {
                'group_name': group['name'],
                'is_required': group['is_required'],
                'options': [{'title': opt['title'], 'price': opt.get('Price')} for opt in group['options']]
            }
            for group in deal.modifiers
        ]
        example_payload = {
            'menu_item_id': deal.id,
            'quantity': quantity
        }
        
        # Only add selected_modifiers to example if there are required modifiers
        required_groups = [group for group in deal.modifiers if group['is_required']]
        if required_groups:
            example_payload['selected_modifiers'] = [
                {
                    'group_name': group['name'],
                    'selected_options': ['Select an option from available options']
                }
                for group in required_groups
            ]
        
        return Response({
            'error': 'Please select required modifiers',
            'required_modifiers': required_modifiers,
            'example_payload': example_payload
        }, status=status.HTTP_400_BAD_REQUEST)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        deal=deal,
        defaults={
            'quantity': quantity,
            'selected_modifiers': selected_modifiers
        }
    )
    
    if not created:
        cart_item.quantity = quantity
        cart_item.selected_modifiers = selected_modifiers
        cart_item.save()

    return Response({
        'message': 'Item added to cart',
        'cart_total': str(cart.final_total),
        'cart_item_id': cart_item.id
    }, status=status.HTTP_201_CREATED)
 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    """Update cart item quantity and modifiers"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = request.data.get('quantity')
    selected_modifiers = request.data.get('selected_modifiers')
    
    if quantity is not None:
        if quantity > 0:
            cart_item.quantity = quantity
        else:
            cart_item.delete()
            return Response({'message': 'Item removed from cart'})
    
    if selected_modifiers is not None:
        # Validate the modifiers
        deal_modifiers = cart_item.deal.modifiers
        required_groups = [group['name'] for group in deal_modifiers if group['is_required']]
        selected_groups = {mod['group_name'] for mod in selected_modifiers}
        
        # Check required groups
        missing_required = set(required_groups) - selected_groups
        if missing_required:
            return Response({
                'error': f'Required modifier groups missing: {", ".join(missing_required)}',
                'required_groups': [
                    {
                        'name': group['name'],
                        'options': [opt['title'] for opt in group['options']]
                    }
                    for group in deal_modifiers
                    if group['name'] in missing_required
                ]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate selections
        for selection in selected_modifiers:
            group = next((g for g in deal_modifiers if g['name'] == selection['group_name']), None)
            if not group:
                return Response({
                    'error': f'Invalid modifier group: {selection["group_name"]}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            available_options = {opt['title'] for opt in group['options']}
            invalid_options = set(selection['selected_options']) - available_options
            if invalid_options:
                return Response({
                    'error': f'Invalid options for {selection["group_name"]}: {", ".join(invalid_options)}',
                    'available_options': list(available_options)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item.selected_modifiers = selected_modifiers
    
    cart_item.save()
    
    return Response({
        'message': 'Cart item updated',
        'cart_item': {
            'id': cart_item.id,
            'quantity': cart_item.quantity,
            'selected_modifiers': cart_item.selected_modifiers,
            'unit_price': str(cart_item.unit_price),
            'item_total': str(cart_item.item_total)
        }
    })
 
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
        subscription = Subscription.objects.filter(user=request.user).last()
        is_subscribed = subscription and subscription.is_active
        
        # Determine which discount value to use based on user's subscription status
        discount_value = None
        if deal.deal_type == 'Both':
            # For 'Both' type, use paid if user is subscribed, otherwise use free
            if is_subscribed:
                discount_value = deal.discount_value_paid
            else:
                discount_value = deal.discount_value_free
        elif deal.deal_type == 'Free':
            discount_value = deal.discount_value_free
        elif deal.deal_type == 'Paid':
            # Only apply paid discount if user is subscribed
            if is_subscribed:
                discount_value = deal.discount_value_paid
            else:
                return Response(
                    {
                        'error': 'This deal is only available for subscribed users',
                        'deal_type': 'Paid',
                        'requires_subscription': True
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

        # Calculate discount based on the type
        discount = Decimal('0.00')
        if discount_value in ['5', '10', '25', '50']:  # Percentage discounts
            percentage = Decimal(discount_value)
            discount = (cart.subtotal * percentage) / Decimal('100.00')
        elif discount_value == '1+1':
            # Buy one get one free - 50% off if buying even number of items
            total_items = sum(item.quantity for item in cart.cart_items.all())
            if total_items % 2 == 0:
                discount = cart.subtotal * Decimal('0.50')
            else:
                discount = (cart.subtotal * Decimal('0.50')) - (cart.subtotal / total_items / Decimal('2.00'))
        elif discount_value == 'FREE ITEM':
            # Find the lowest priced item and make it free
            min_price_item = min(cart.cart_items.all(), key=lambda x: x.unit_price)
            discount = min_price_item.unit_price
            
        checkout_data.update({
            'discount_amount': str(discount),
            'final_total': str(cart.subtotal + cart.delivery_fee - discount),
            'applied_deal': {
                'id': deal.id,
                'title': deal.title,
                'deal_type': deal.deal_type,
                'discount_value': discount_value,
                'is_subscribed': is_subscribed
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
    payment_method = request.data.get('payment_method', 'MOLLIE')
    
    if not cart.cart_items.exists():
        return Response(
            {'error': 'Cannot create order with empty cart'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate all cart items have required modifiers before proceeding
    for cart_item in cart.cart_items.all():
        print(f"Checking item {cart_item.id}: {cart_item.deal.title}")
        print(f"Required modifiers in deal: {[g['name'] for g in cart_item.deal.modifiers if g['is_required']]}")
        print(f"Current selections: {cart_item.selected_modifiers}")
        
        try:
            cart_item.validate_modifiers()
        except ValueError as e:
            # Return more helpful error message with available options
            missing_group_name = str(e).split("'")[1]  # Extract group name from error message
            group_info = next((g for g in cart_item.deal.modifiers if g['name'] == missing_group_name), None)
            
            return Response({
                'error': str(e),
                'cart_item_id': cart_item.id,
                'deal_name': cart_item.deal.title,
                'missing_group': {
                    'name': missing_group_name,
                    'available_options': [opt['title'] for opt in group_info['options']] if group_info else []
                }
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Calculate totals including deal if provided
    subtotal = cart.subtotal     
    delivery_fee = cart.delivery_fee
    discount_amount = Decimal('0.00')
    subscription = Subscription.objects.filter(user=request.user).last()
    is_subscribed = subscription and subscription.is_active
    
    if deal_id:
        deal = get_object_or_404(Create_Deal, id=deal_id)
        
        # Determine which discount value to use based on user's subscription status
        discount_value = None
        if deal.deal_type == 'Both':
            # For 'Both' type, use paid if user is subscribed, otherwise use free
            if is_subscribed:
                discount_value = deal.discount_value_paid
            else:
                discount_value = deal.discount_value_free
        elif deal.deal_type == 'Free':
            discount_value = deal.discount_value_free
        elif deal.deal_type == 'Paid':
            # Only apply paid discount if user is subscribed
            if is_subscribed:
                discount_value = deal.discount_value_paid
            else:
                return Response(
                    {'error': 'This deal is only available for subscribed users'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Calculate discount based on the type
        if discount_value in ['5', '10', '25', '50']:  # Percentage discounts
            percentage = Decimal(discount_value)
            discount_amount = (subtotal * percentage) / Decimal('100.00')
        elif discount_value == '1+1':
            # Buy one get one free - 50% off if buying even number of items
            total_items = sum(item.quantity for item in cart.cart_items.all())
            if total_items % 2 == 0:
                discount_amount = subtotal * Decimal('0.50')
            else:
                discount_amount = (subtotal * Decimal('0.50')) - (subtotal / total_items / Decimal('2.00'))
        elif discount_value == 'FREE ITEM':
            # Find the lowest priced item and make it free
            min_price_item = min(cart.cart_items.all(), key=lambda x: x.unit_price)
            discount_amount = min_price_item.unit_price
        else:
            # For other special cases like PRE ORDER, LATE NIGHT, QOUPON+
            # You can implement specific logic for each case
            discount_amount = Decimal('0.00')
    
    total_amount = subtotal + delivery_fee - discount_amount
    
    # Create cart snapshot
    cart_data = {
        'items': [{
            'deal_id': item.deal.id,
            'title': item.deal.title,
            'quantity': item.quantity,
            'unit_price': str(item.unit_price),
            'total': str(item.item_total),
            'image': item.deal.image.url if item.deal.image else None,
            'modifiers': [{
                'name': modifier_group['name'],
                'is_required': modifier_group['is_required'],
                'selections': [
                    {
                        'title': option['title'],
                        'price': str(option.get('Price', '0.00'))
                    }
                    for option in modifier_group['options']
                    if any(selection == option['title'] 
                          for selection in next((s['selected_options'] 
                                               for s in item.selected_modifiers 
                                               if s['group_name'] == modifier_group['name']), 
                                              []))
                ]
            } for modifier_group in item.deal.modifiers]
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
    
    # Set initial order status based on payment method
    # For cash payment: Order is RECEIVED but payment stays PENDING until delivery verification
    initial_status = Order.OrderStatus.RECEIVED if payment_method == Order.PaymentMethod.CASH else Order.OrderStatus.PENDING_PAYMENT
    initial_payment_status = Order.PaymentStatus.PENDING  # Payment status stays pending for both cash and online payments
    
    order = Order.objects.create(
        user=request.user,
        cart_snapshot=cart_data,
        delivery_type=request.data.get('delivery_type'),
        order_type=request.data.get('order_type'),
        scheduled_datetime=request.data.get('scheduled_datetime'),
        delivery_address=request.data.get('delivery_address'),
        special_instructions=request.data.get('special_instructions'),
        note=request.data.get('note', ''),
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        discount_amount=discount_amount,
        total_amount=total_amount,
        status=initial_status,
        payment_method=payment_method,
        payment_status=initial_payment_status
    )
    
    # Create order items
    for cart_item in cart.cart_items.all():
        # Validate required modifiers
        try:
            cart_item.validate_modifiers()
        except ValueError as e:
            # Roll back the transaction
            transaction.set_rollback(True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create order item with selected modifiers
        order_item = OrderItem.objects.create(
            order=order,
            deal=cart_item.deal,
            quantity=cart_item.quantity,
            item_name=cart_item.deal.title,
            item_description=cart_item.deal.description,
            selected_modifiers=cart_item.selected_modifiers,  # Copy JSON-based modifiers directly
            unit_price=cart_item.unit_price,
            modifiers_price=cart_item.modifiers_price,
            total_price=cart_item.item_total
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
        deal.redemption += 1
        deal.save()
    
    # Create initial tracking with appropriate message
    tracking_note = 'Order received (Cash payment)' if payment_method == Order.PaymentMethod.CASH else 'Order created, awaiting payment'
    OrderTracking.objects.create(
        order=order,
        status=order.status,
        note=tracking_note
    )
    
    # Send notification to customer
    notification_message = (
        f"Your order #{order.order_id} has been received (Cash payment)" 
        if payment_method == Order.PaymentMethod.CASH
        else f"Your order #{order.order_id} has been created and is awaiting payment"
    )
    
    FirebaseNotification.send_to_user(
        user=request.user,
        title="Order Created",
        body=notification_message,
        data={
            'order_id': str(order.order_id),
            'status': order.status,
            'type': 'order_created',
            'payment_method': payment_method
        },
        notification_type='order_status'
    )
    
    # If it's a cash payment, notify vendors immediately since order is received
    if payment_method == Order.PaymentMethod.CASH:
        for vendor_id in order.items.values_list('deal__user', flat=True).distinct():
            try:
                vendor = type(order.user).objects.get(id=vendor_id)
                FirebaseNotification.send_to_user(
                    user=vendor,
                    title="New Order Received",
                    body=f"You have received a new order #{order.order_id} (Cash payment)",
                    data={
                        'order_id': str(order.order_id),
                        'status': order.status,
                        'type': 'new_order',
                        'payment_method': 'CASH'
                    },
                    notification_type='order_status'
                )
            except Exception as e:
                logger.error(f"Failed to send vendor notification: {e}")

    serializer = OrderSerializer(order)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_payment(request, order_id):
    """Process payment using Mollie payment gateway"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    redirect_url = request.data.get('redirect_url')
    
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
            'redirectUrl': redirect_url if redirect_url else f'https://dummy.org/orders/{order.order_id}/confirmation/',
            'webhookUrl': request.build_absolute_uri('/order/webhook/mollie/'),
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
    """Cancel an order - Both customers and vendors can cancel orders"""
    order = get_object_or_404(Order, order_id=order_id)
    cancellation_reason = request.data.get('cancellation_reason', '')
    
    # Check if user is a vendor
    is_vendor = False
    try:
        vendor_profile = Business_profile.objects.get(owner=request.user)
        # Verify vendor has items in this order
        if order.items.filter(deal__user=request.user).exists():
            is_vendor = True
    except Business_profile.DoesNotExist:
        pass
    
    # If not vendor, must be the order owner
    if not is_vendor and order.user != request.user:
        raise PermissionDenied("You can only cancel your own orders")
    
    if order.status in [Order.OrderStatus.COMPLETED, Order.OrderStatus.CANCELLED]:
        return Response(
            {'error': 'Cannot cancel completed or already cancelled orders'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    order.status = Order.OrderStatus.CANCELLED
    order.save()
    
    # Set appropriate cancellation note based on who cancelled
    if is_vendor:
        note = f"Order cancelled by vendor {vendor_profile.name}: {cancellation_reason}" if cancellation_reason else f"Order cancelled by vendor {vendor_profile.name}"
    else:
        note = f"Order cancelled by customer: {cancellation_reason}" if cancellation_reason else "Order cancelled by customer"
    
    OrderTracking.objects.create(
        order=order,
        status=Order.OrderStatus.CANCELLED,
        note=note
    )

    # Send notification based on who cancelled the order
    if is_vendor:
        # Notify customer
        FirebaseNotification.send_to_user(
            user=order.user,
            title="Order Cancelled",
            body=f"Your order #{order.order_id} has been cancelled by vendor: {cancellation_reason if cancellation_reason else 'No reason provided'}",
            data={
                'order_id': str(order.order_id),
                'status': Order.OrderStatus.CANCELLED,
                'type': 'order_cancelled',
                'cancelled_by': 'vendor',
                'reason': cancellation_reason
            },
            notification_type='order_status'
        )

        # Notify other vendors if any
        for vendor_id in order.items.values_list('deal__user', flat=True).distinct():
            if vendor_id != request.user.id:  # Don't notify the cancelling vendor
                try:
                    other_vendor = type(order.user).objects.get(id=vendor_id)
                    FirebaseNotification.send_to_user(
                        user=other_vendor,
                        title="Order Cancelled",
                        body=f"Order #{order.order_id} has been cancelled by another vendor: {cancellation_reason if cancellation_reason else 'No reason provided'}",
                        data={
                            'order_id': str(order.order_id),
                            'status': Order.OrderStatus.CANCELLED,
                            'type': 'order_cancelled',
                            'cancelled_by': 'vendor',
                            'reason': cancellation_reason
                        },
                        notification_type='order_status'
                    )
                except Exception as e:
                    logger.error(f"Failed to send vendor notification: {e}")
    else:
        # Customer cancelled - notify all vendors
        for vendor_id in order.items.values_list('deal__user', flat=True).distinct():
            try:
                vendor = type(order.user).objects.get(id=vendor_id)
                FirebaseNotification.send_to_user(
                    user=vendor,
                    title="Order Cancelled",
                    body=f"Order #{order.order_id} has been cancelled by the customer: {cancellation_reason if cancellation_reason else 'No reason provided'}",
                    data={
                        'order_id': str(order.order_id),
                        'status': Order.OrderStatus.CANCELLED,
                        'type': 'order_cancelled',
                        'cancelled_by': 'customer',
                        'reason': cancellation_reason
                    },
                    notification_type='order_status'
                )
            except Exception as e:
                logger.error(f"Failed to send vendor notification: {e}")
    
    return Response({
        'message': 'Order cancelled successfully',
        'cancelled_by': 'vendor' if is_vendor else 'customer',
        'reason': cancellation_reason if cancellation_reason else None
    })
 
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
@permission_classes([])  # No authentication required for webhook - this is called by Mollie's servers
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

            # Send notification to customer
            FirebaseNotification.send_payment_update(order, "successful")

            # Notify vendor(s)
            for vendor_id in order.items.values_list('deal__user', flat=True).distinct():
                try:
                    vendor = type(order.user).objects.get(id=vendor_id)
                    FirebaseNotification.send_to_user(
                        user=vendor,
                        title="New Order Received",
                        body=f"You have received a new order #{order.order_id}",
                        data={
                            'order_id': str(order.order_id),
                            'status': order.status,
                            'type': 'new_order'
                        },
                        notification_type='order_status'
                    )
                except Exception as e:
                    logger.error(f"Failed to send vendor notification: {e}")
            
        elif payment.is_canceled():
            order.status = Order.OrderStatus.CANCELLED
            order.payment_status = Order.PaymentStatus.CANCELLED
            order.save()
            
            OrderTracking.objects.create(
                order=order,
                status=Order.OrderStatus.CANCELLED,
                note='Payment was cancelled'
            )

            FirebaseNotification.send_payment_update(order, "cancelled")
            
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
    if new_status == Order.OrderStatus.READY_FOR_PICKUP:
        if order.delivery_type != Order.DeliveryType.PICKUP:
            return Response(
                {'error': 'READY_FOR_PICKUP status is only valid for pickup orders'},
                status=status.HTTP_400_BAD_REQUEST
            )
 
        elif new_status == Order.OrderStatus.OUT_FOR_DELIVERY:
            if order.delivery_type != Order.DeliveryType.DELIVERY:
                return Response(
                    {'error': 'OUT_FOR_DELIVERY status is only valid for delivery orders'},
                    status=status.HTTP_400_BAD_REQUEST
                )
    
    if order.status not in allowed_transitions or new_status not in allowed_transitions[order.status]:
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

    # Send notification to customer
    status_messages = {
        Order.OrderStatus.PREPARING: 'is being prepared',
        Order.OrderStatus.READY_FOR_PICKUP: 'is ready for pickup',
        Order.OrderStatus.OUT_FOR_DELIVERY: 'is out for delivery'
    }

    if new_status in status_messages:
        FirebaseNotification.send_order_status_update(order, status_messages[new_status])
    
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

    # Update payment status for cash payments
    if order.payment_method == Order.PaymentMethod.CASH:
        order.payment_status = Order.PaymentStatus.PAID
        payment_note = ' - Cash payment received'
    else:
        payment_note = ''

    order.save()
    
    # Create tracking entry
    OrderTracking.objects.create(
        order=order,
        status=Order.OrderStatus.COMPLETED,
        note=f'Order completed - verified via QR code{payment_note}'
    )

    # Send notification to customer
    notification_msg = (
        f"Your order #{order.order_id} has been completed and payment received"
        if order.payment_method == Order.PaymentMethod.CASH
        else f"Your order #{order.order_id} has been completed"
    )
    
    FirebaseNotification.send_to_user(
        user=order.user,
        title="Order Completed",
        body=notification_msg,
        data={
            'order_id': str(order.order_id),
            'status': order.status,
            'payment_status': order.payment_status,
            'type': 'order_completed',
            'payment_method': order.payment_method
        },
        notification_type='order_status'
    )

    # Notify vendor(s)
    for vendor_id in order.items.values_list('deal__user', flat=True).distinct():
        try:
            vendor = type(order.user).objects.get(id=vendor_id)
            
            # Different message for cash payments
            vendor_msg = (
                f"Order #{order.order_id} has been completed successfully and cash payment received"
                if order.payment_method == Order.PaymentMethod.CASH
                else f"Order #{order.order_id} has been completed successfully"
            )
            
            FirebaseNotification.send_to_user(
                user=vendor,
                title="Order Completed",
                body=vendor_msg,
                data={
                    'order_id': str(order.order_id),
                    'status': order.status,
                    'payment_status': order.payment_status,
                    'type': 'order_completed',
                    'payment_method': order.payment_method
                },
                notification_type='order_status'
            )
        except Exception as e:
            logger.error(f"Failed to send vendor notification: {e}")
    
    return Response({
        'message': 'Delivery verified and order completed successfully',
        'order_status': order.status
    })



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_estimated_delivery_time(request, order_id):
    """Update estimated delivery time for an order"""
    order = get_object_or_404(Order, order_id=order_id)
 
    if order.status not in [Order.OrderStatus.PREPARING, Order.OrderStatus.READY_FOR_PICKUP, Order.OrderStatus.OUT_FOR_DELIVERY]:
        return Response(
            {'error': 'Cannot update estimated delivery time for this order status'},
            status=status.HTTP_400_BAD_REQUEST
        )
 
    estimated_delivery_time = request.data.get('estimated_delivery_time')
    if not estimated_delivery_time:
        return Response(
            {'error': 'Estimated delivery time is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
 
    order.estimated_delivery_time = estimated_delivery_time
    order.save()
 
    return Response({
        'message': 'Estimated delivery time updated successfully',
        'estimated_delivery_time': estimated_delivery_time
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vendor_orders(request):
    """Get all orders for a vendor"""
    try:
        vendor_profile = Business_profile.objects.get(owner=request.user)
    except Business_profile.DoesNotExist:
        raise PermissionDenied("Only vendors can access orders")

    # Get all orders that have items from this vendor
    orders = Order.objects.filter(items__deal__user=request.user).distinct()
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)
 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vendor_order_detail(request, order_id):
    """Get a single order for a vendor"""
    try:
        vendor_profile = Business_profile.objects.get(owner=request.user)
    except Business_profile.DoesNotExist:
        raise PermissionDenied("Only vendors can access orders")

    # Get the order only if it has items from this vendor
    order = get_object_or_404(Order, order_id=order_id, items__deal__user=request.user)
    serializer = OrderSerializer(order)
    return Response(serializer.data)
 