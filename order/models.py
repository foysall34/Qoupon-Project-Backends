from django.db import models
from django.conf import settings
from django.utils import timezone
from vendors.models import Create_Deal, Deal
from decimal import Decimal
from QrCodeApp.models import QRCode
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
    def final_total(self):
        return self.subtotal
    
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
    selected_modifiers = models.JSONField(default=list, blank=True,
        help_text='''Format: [
            {
                "group_name": "Select Your Bread",
                "selected_options": ["Classic Bread"]
            }
        ]''')
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    @property
    def modifiers_price(self):
        total_modifier_price = Decimal('0.00')
        # Get the modifiers configuration from the deal
        modifier_groups = self.deal.modifiers
        # Get the user's selections
        selections = {item['group_name']: item['selected_options'] for item in self.selected_modifiers}
        
        # Calculate price for each selected modifier
        for group in modifier_groups:
            group_name = group['name']
            if group_name in selections:
                selected_options = selections[group_name]
                for option in group['options']:
                    if option['title'] in selected_options and option.get('Price') is not None:
                        total_modifier_price += Decimal(str(option['Price']))
        
        return total_modifier_price

    @property
    def unit_price(self):
        # Base price of the deal plus all modifier prices
        return self.deal.price + self.modifiers_price

    def validate_modifiers(self):
        """Validate that required modifier groups have selections"""
        selections = {item['group_name']: item['selected_options'] for item in self.selected_modifiers}
        
        for group in self.deal.modifiers:
            if group['is_required'] and (
                group['name'] not in selections or 
                not selections[group['name']]
            ):
                raise ValueError(f"Required modifier group '{group['name']}' must have a selection")
 
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
        CANCELLED = 'CANCELLED', 'Cancelled'

    payment_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
 
    class DeliveryType(models.TextChoices):
        PICKUP = 'PICKUP', 'Pickup'
        DELIVERY = 'DELIVERY', 'Delivery'
    
    class OrderType(models.TextChoices):
        STANDARD = 'STANDARD', 'Standard Order'
        SCHEDULED = 'SCHEDULED', 'Scheduled Order'
    
    class PaymentMethod(models.TextChoices):
        MOLLIE = 'MOLLIE', 'Mollie'
        CASH = 'CASH', 'Cash on Delivery/Pickup'
        
 
    order_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_orders')
    cart_snapshot = models.JSONField(null=True, blank=True,
        help_text="Snapshot of cart data at time of order")
    
    # Order Status
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.RECEIVED)
    payment_method = models.CharField(max_length=50, choices=PaymentMethod.choices, null=True, blank=True, default=PaymentMethod.MOLLIE)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    delivery_type = models.CharField(max_length=10, choices=DeliveryType.choices)
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.FloatField(default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Address for delivery
    delivery_address = models.TextField(blank=True, null=True)
    delivery_address_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_address_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Order Type and Scheduling
    order_type = models.CharField(max_length=10, choices=OrderType.choices, default=OrderType.STANDARD)
    scheduled_datetime = models.DateTimeField(null=True, blank=True,
        help_text="Required if order_type is SCHEDULED. When the order should be delivered/ready for pickup.")
    
    # Additional Info
    special_instructions = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    estimated_delivery_time = models.DurationField(null=True, blank=True)
    
    # Delivery Verification
    delivery_code = models.CharField(max_length=6, unique=True, null=True, blank=True,
                                   help_text="Unique code for delivery QR verification")
    delivery_code_created_at = models.DateTimeField(null=True, blank=True)
    delivery_code_used = models.BooleanField(default=False)
    qr_code = models.OneToOneField(QRCode, on_delete=models.SET_NULL, null=True, blank=True, related_name='order')
 
    def generate_delivery_code(self):
        """Generate a unique 6-digit delivery verification code"""
        while True:
            # Generate a random 6-digit number
            code = ''.join(secrets.choice('0123456789') for _ in range(6))
            
            # Check if code is unique
            if not Order.objects.filter(delivery_code=code).exists():
                return code
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            old_status = Order.objects.only("status").get(pk=self.pk).status
 
        # New order → generate delivery code if missing
        if is_new and not self.delivery_code:
            self.delivery_code = self.generate_delivery_code()
            self.delivery_code_created_at = timezone.now()
 
        # Generate QR code for new RECEIVED orders or when status changes to RECEIVED
        if (
            (is_new and self.status == self.OrderStatus.RECEIVED) or
            (old_status and old_status != self.OrderStatus.RECEIVED and self.status == self.OrderStatus.RECEIVED)
        ):
            if not self.delivery_code:
                self.delivery_code = self.generate_delivery_code()
                self.delivery_code_created_at = timezone.now()
            if not self.qr_code and not self.delivery_code_used:
                from django.core.files.base import ContentFile
                import qrcode
                from io import BytesIO
 
                qr = qrcode.make(self.delivery_code)
                buffer = BytesIO()
                qr.save(buffer, format="PNG")
                file_name = f"qr_{self.order_id}.png"
 
                qr_code = QRCode(user=self.user, data=self.delivery_code)
                qr_code.save()
                qr_code.image.save(file_name, ContentFile(buffer.getvalue()), save=True)
                self.qr_code = qr_code
 
        # Status changed to CANCELLED or COMPLETED → delete QR code (if exists)
        if (
            old_status
            and old_status not in [self.OrderStatus.CANCELLED, self.OrderStatus.COMPLETED]
            and self.status in [self.OrderStatus.CANCELLED, self.OrderStatus.COMPLETED]
        ):
            if self.qr_code:
                self.qr_code.delete()
                self.qr_code = None
 
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
    item_image = models.ImageField(upload_to='order_items/', blank=True)
    note = models.TextField(blank=True)
    
    # Store selected modifiers and ingredients
    selected_modifiers = models.JSONField(default=dict, blank=True,
        help_text="Format: {'modifier_group_id': {'name': 'group_name', 'required': bool, 'selections': [{'id': id, 'name': 'name', 'price': price}]}}")
    modifiers_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if not self.pk and self.deal:  # New order item
            self.item_name = self.deal.title
            self.item_description = self.deal.description
            
            # Base price is deal price
            base_price = self.deal.price
            
            # Store current state of selected modifiers if not already stored
            if not self.selected_modifiers and hasattr(self, 'cart_item'):
                modifier_data = {}
                for group in self.cart_item.selected_modifier_groups.all():
                    selections = self.cart_item.selected_modifiers.filter(modifier_groups=group)
                    if selections.exists():
                        modifier_data[str(group.id)] = {
                            'name': group.name,
                            'required': group.is_required,
                            'selections': [
                                {
                                    'id': mod.id,
                                    'name': mod.name,
                                    'price': str(mod.price)
                                }
                                for mod in selections
                            ]
                        }
                self.selected_modifiers = modifier_data
                
                # Calculate modifiers price
                self.modifiers_price = sum(
                    Decimal(mod['price'])
                    for group in self.selected_modifiers.values()
                    for mod in group['selections']
                )
            
            # Calculate final prices
            self.unit_price = base_price + self.modifiers_price
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