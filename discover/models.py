from django.db import models
from cloudinary.models import CloudinaryField
from django.conf import settings
from django.utils import timezone


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
    review_count = models.CharField(max_length=20, default="500+")
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
    


# QR Scanner code 
class CoffeeSubscriptionOffer(models.Model):
    title = models.CharField(max_length=100, default="Pret Coffee Subscription")
    description = models.TextField(default="All your organic coffees (and teas, frappes, hot chocolates...)")
    price_details = models.CharField(max_length=100, default="for £20 a month")
    offer_details = models.CharField(max_length=100, default="and your first month FREE")
    website_url = models.URLField(default="http://PretCoffeeSub.co.uk")
    is_active = models.BooleanField(default=True) # অফারটি সক্রিয় কিনা তা ট্র্যাক করার জন্য
    expiry_date = models.DateTimeField() # অফারের মেয়াদ শেষ হওয়ার তারিখ ও সময়

    def __str__(self):
        return self.title

    def is_expired(self):
        """মেয়াদ শেষ হয়েছে কিনা তা পরীক্ষা করে"""
        return timezone.now() > self.expiry_date
    
# Edit profile 

