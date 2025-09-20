from django.db import models
from cloudinary.models import CloudinaryField
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from django.db import models
from django.conf import settings
from decimal import Decimal

import random
import string

class Cuisine(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Diet(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    logo = CloudinaryField('image', blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    review_count = models.IntegerField()
    distance_km = models.DecimalField(max_digits=4, decimal_places=1)
    tags = models.CharField(max_length=255, help_text="Comma-separated tags e.g., Vegan, Gezond, Pizza")
    discount_percentage = models.IntegerField(default=0)
    cuisines = models.ManyToManyField(Cuisine, related_name='restaurants')
    diets = models.ManyToManyField(Diet, related_name='restaurants')
    average_price = models.DecimalField(max_digits=6, decimal_places=2, help_text="Average price for one person" , blank=True , null= True)

    def __str__(self):
        return self.name
    
class Offer(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = CloudinaryField('image')
    valid_until = models.DateTimeField()
    discount_percentage = models.IntegerField()
    
    redemption_methods = models.CharField(max_length=100, help_text="e.g., Delivery & Pickup")
    delivery_cost = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    min_order_amount = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    restaurant = models.ForeignKey('Restaurant', on_delete=models.CASCADE, related_name='offers')
    favorited_by = models.ManyToManyField(settings.AUTH_USER_MODEL , related_name='favorite_offers', blank=True)

    def __str__(self):
        return self.title
    


class CoffeeSubscriptionOffer(models.Model):
    title = models.CharField(max_length=100, default="Pret Coffee Subscription")
    description = models.TextField(default="All your organic coffees (and teas, frappes, hot chocolates...)")
    price_details = models.CharField(max_length=100, default="for £20 a month")
    offer_details = models.CharField(max_length=100, default="and your first month FREE")
    website_url = models.URLField(default="http://PretCoffeeSub.co.uk")
    is_active = models.BooleanField(default=True) 
    expiry_date = models.DateTimeField()

    def __str__(self):
        return self.title

    def is_expired(self):
        return timezone.now() > self.expiry_date
    




class OrderStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class OrderType(models.TextChoices):
    DELIVERY = 'delivery', 'Delivery'
    PICKUP = 'pickup', 'Pickup'

def generate_order_id():
    length = 8
  
    chars = string.ascii_uppercase + string.digits
    while True:
        order_id = ''.join(random.choices(chars, k=length))
        if not Order.objects.filter(order_id=order_id).exists():
            break
    return order_id

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL , on_delete=models.CASCADE, related_name='orders')
    order_id = models.CharField(max_length=100, unique=True , blank= True)
    product_name = models.CharField(max_length=255)
    product_image = CloudinaryField('image')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.ACTIVE
    )
    order_type = models.CharField(
        max_length=20,
        choices=OrderType.choices,
        default=OrderType.DELIVERY
    )
    created_at = models.DateTimeField(auto_now_add=True)


    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = generate_order_id()
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.order_id} - {self.product_name}"
    








User = settings.AUTH_USER_MODEL

# ------------------------- Menu + add to cart  ---------------------------

class MenuCategory(models.Model):
    name = models.CharField(max_length=100, unique=True , null=True)
    user = models.ForeignKey(User,on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Menu Categories" 

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    category = models.ForeignKey(MenuCategory,on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200 , null=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    calories = models.PositiveIntegerField(null=True, blank=True)
    image = CloudinaryField('image', null=True, blank=True)
    added_to_cart = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ReviewMenuItem(models.Model):
    RATING_CHOICES = [
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    ]
    menu_item = models.ForeignKey(MenuItem, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user} for {self.menu_item.name}"   



class OptionGroup(models.Model):
    item = models.ForeignKey(MenuItem, related_name='option_title', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    is_required = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} for {self.item.name}"

class OptionChoice(models.Model):
    group = models.ForeignKey(OptionGroup, related_name='options', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    selected_title = models.CharField(max_length=200 , default='write title')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_selected = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} (+{self.price})"

# for cart **************************************************************************************************************

class Cart(models.Model):
    class DeliveryType(models.TextChoices):
        PICKUP = 'PICKUP', 'Pickup'
        DELIVERY = 'DELIVERY', 'Delivery'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivery_type = models.CharField(max_length=10, choices=DeliveryType.choices, default=DeliveryType.DELIVERY)

    @property
    def sub_total_price(self):
        return sum((item.total_price for item in self.items.all()), start=Decimal(0))

    @property
    def delivery_charges(self) -> Decimal:
        if self.delivery_type == self.DeliveryType.DELIVERY:
            return Decimal("1.99")
        return Decimal("0.00") # No charge to declared for pickUp

    @property
    def in_total_price(self):
        """
        'In total price (delivery charge + sub total price)'।
        """
        return self.sub_total_price + self.delivery_charges

    def __str__(self):
        return f"Cart for {self.user.email}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    selected_options = models.ManyToManyField(OptionChoice, blank=True)

    @property
    def add_to_cart_price(self):
        """
       'add to cart price (without quantity)'।
        """
        base_price = self.menu_item.price
        options_price = sum((option.price for option in self.selected_options.all()),start=Decimal(0))
        return base_price + options_price

    @property
    def total_price(self):
        return self.add_to_cart_price * self.quantity

    def increase_quantity(self, amount: int = 1):

        self.quantity += amount
        self.save()

    def decrease_quantity(self, amount: int = 1):
        """
    Decreased the cart quantity if (0 then cart will be deleted automatically)
        """
        if self.quantity <= amount:
            self.delete()
        else:
            self.quantity -= amount
            self.save()

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name} in {self.cart}"





   

class VendorFollowed(models.Model):
    menu_category = models.ForeignKey(MenuCategory,on_delete=models.CASCADE, related_name='vendors')
    title = models.CharField(max_length=200 , default='title' , blank= True, null= True)
    logo = CloudinaryField('image')
    category = models.CharField(max_length=100)
    descriptions = models.CharField(max_length=200)
    expiry_date = models.DateTimeField(default=timezone.now)
    is_followed = models.BooleanField(default=False)
    

    def __str__(self):
        return self.category


