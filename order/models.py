from django.db import models
from django.conf import settings
from django.utils import timezone
from vendors.models import Create_Deal, Deal
from decimal import Decimal
import uuid
import secrets
 
class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shopping_cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.cart_items.all())
    
    @property
    def subtotal(self):
        return sum(item.item_total for item in self.cart_items.all())
    
    @property
    def delivery_fee(self):
        # Can be made more sophisticated based on distance, order value, etc.
        base_delivery_fee = Decimal('2.99')
        if self.subtotal > Decimal('25.00'):  # Free delivery over $25
            return Decimal('0.00')
        return base_delivery_fee
    
    @property
    def final_total(self):
        return self.subtotal + self.delivery_fee
    
    def clear(self):
        self.cart_items.all().delete()
        if hasattr(self, 'applied_deal'):
            self.applied_deal.delete()
    
    def __str__(self):
        return f"Cart for {self.user.email}"
 
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='order_cart_items')
    quantity = models.PositiveIntegerField(default=1)
    special_instructions = models.TextField(blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    @property
    def unit_price(self):
        return self.deal.price
 
    @property
    def item_total(self):
        return self.unit_price * self.quantity
 
    def __str__(self):
        return f"{self.quantity}x {self.deal.title}"
 
class CartDeal(models.Model):
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE, related_name='applied_deal')
    deal = models.ForeignKey(Create_Deal, on_delete=models.CASCADE)
    applied_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def calculated_discount(self):
        """
        Calculate the discount amount based on the deal and cart contents
        """
        if not self.deal or not self.cart:
            return Decimal('0.00')
        
        discount = self.deal.discount_value
        cart_subtotal = self.cart.subtotal
        
        # Apply the discount
        if discount <= 100:  # Percentage discount
            return (cart_subtotal * discount) / Decimal('100.00')
        return min(discount, cart_subtotal)  # Fixed amount discount
    
    def __str__(self):
        return f"{self.deal.title} applied to {self.cart}"
 
class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING_PAYMENT = 'PENDING_PAYMENT', 'Pending Payment'
        RECEIVED = 'RECEIVED', 'Order Received'
        PREPARING = 'PREPARING', 'In Preparation'
        OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY', 'Out for Delivery'
        READY_FOR_PICKUP = 'READY_FOR_PICKUP', 'Ready for Pick Up'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'
 
    class DeliveryType(models.TextChoices):
        PICKUP = 'PICKUP', 'Pickup'
        DELIVERY = 'DELIVERY', 'Delivery'
    
    class OrderType(models.TextChoices):
        STANDARD = 'STANDARD', 'Standard Order'
        SCHEDULED = 'SCHEDULED', 'Scheduled Order'
 
    order_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_orders')
    cart_snapshot = models.JSONField(null=True, blank=True,
        help_text="Snapshot of cart data at time of order")
    
    # Order Status
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.RECEIVED)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    delivery_type = models.CharField(max_length=10, choices=DeliveryType.choices)
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Address for delivery
    delivery_address = models.TextField(blank=True, null=True)
    delivery_postal_code = models.CharField(max_length=10, blank=True, null=True)
    
    # Order Type and Scheduling
    order_type = models.CharField(max_length=10, choices=OrderType.choices, default=OrderType.STANDARD)
    scheduled_datetime = models.DateTimeField(null=True, blank=True,
        help_text="Required if order_type is SCHEDULED. When the order should be delivered/ready for pickup.")
    
    # Additional Info
    special_instructions = models.TextField(blank=True, null=True)
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    
    # Delivery Verification
    delivery_code = models.CharField(max_length=6, unique=True, null=True, blank=True,
                                   help_text="Unique code for delivery QR verification")
    delivery_code_created_at = models.DateTimeField(null=True, blank=True)
    delivery_code_used = models.BooleanField(default=False)
 
    def generate_delivery_code(self):
        """Generate a unique 6-digit delivery verification code"""
        while True:
            # Generate a random 6-digit number
            code = ''.join(secrets.choice('0123456789') for _ in range(6))
            
            # Check if code is unique
            if not Order.objects.filter(delivery_code=code).exists():
                return code
    
    def save(self, *args, **kwargs):
        if not self.pk:  # New order
            if self.cart:
                self.subtotal = self.cart.sub_total_price
                self.delivery_fee = self.cart.delivery_charges
                self.total_amount = self.cart.in_total_price - self.discount_amount
 
        # Generate delivery code when order status changes to PREPARING
        if self.pk:  # Existing order
            old_order = Order.objects.get(pk=self.pk)
            if old_order.status != Order.OrderStatus.PREPARING and self.status == Order.OrderStatus.PREPARING:
                if not self.delivery_code:  # Only generate if not already exists
                    self.delivery_code = self.generate_delivery_code()
                    self.delivery_code_created_at = timezone.now()
                    self.delivery_code_used = False
        
        super().save(*args, **kwargs)
 
    def __str__(self):
        return f"Order {self.order_id} - {self.user.email}"
 
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    deal = models.ForeignKey(Deal, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Store item details at time of order
    item_name = models.CharField(max_length=255)
    item_description = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.pk and self.deal:  # New order item
            self.item_name = self.deal.title
            self.item_description = self.deal.description
            self.unit_price = self.deal.price
            self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
 
    def __str__(self):
        return f"{self.quantity}x {self.item_name} in Order {self.order.order_id}"
 
class AppliedDeal(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='applied_deals')
    deal = models.ForeignKey(Create_Deal, on_delete=models.SET_NULL, null=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Store deal details at time of order
    deal_title = models.CharField(max_length=255)
    deal_description = models.TextField()
    
    def save(self, *args, **kwargs):
        if not self.pk and self.deal:
            self.deal_title = self.deal.title
            self.deal_description = self.deal.description
        super().save(*args, **kwargs)
 
    def __str__(self):
        return f"{self.deal_title} applied to Order {self.order.order_id}"
 
class OrderTracking(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tracking_history')
    status = models.CharField(max_length=20, choices=Order.OrderStatus.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)
 
    class Meta:
        ordering = ['-timestamp']
 
    def __str__(self):
        return f"Order {self.order.order_id} - {self.status} at {self.timestamp}"