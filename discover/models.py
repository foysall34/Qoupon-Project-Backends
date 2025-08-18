from django.db import models
from cloudinary.models import CloudinaryField
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    




# প্রতিটি অর্ডারের স্ট্যাটাস নির্ধারণ করার জন্য
class OrderStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'

# অর্ডারের ধরন নির্ধারণ করার জন্য
class OrderType(models.TextChoices):
    DELIVERY = 'delivery', 'Delivery'
    PICKUP = 'pickup', 'Pickup'

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL , on_delete=models.CASCADE, related_name='orders')
    order_id = models.CharField(max_length=100, unique=True)
    product_name = models.CharField(max_length=255)
    # এখানে ImageField ব্যবহার করা যেতে পারে, তবে উদাহরণের জন্য URLField সহজ
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

    def __str__(self):
        return f"{self.order_id} - {self.product_name}"
    



class VendorFollowed(models.Model):
    title = models.CharField(max_length=200 , default='title' , blank= True, null= True)
    logo = CloudinaryField('image')
    category = models.CharField(max_length=100)
    descriptions = models.CharField(max_length=200)
    expiry_date = models.DateTimeField(default=timezone.now)
    is_followed = models.BooleanField(default=False)
    

    def __str__(self):
        return self.category





class MenuCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Menu Categories"

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    category = models.ForeignKey(
        MenuCategory, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    calories = models.PositiveIntegerField()
    image = CloudinaryField('image')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name



