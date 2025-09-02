
from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = CloudinaryField('image', blank=True, null=True)

    def __str__(self):
        return self.name

class Shop(models.Model):
    Redemption_CHOICES = (
        ('Delivery', 'Delivery'),
        ('Pickup', 'Pickup'),
        ('Delivery & Pickup', 'Delivery & Pickup'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='myuser' ,null= True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, related_name='shops', on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True, null=True)
    
    # "Shops Near You" 
    logo = CloudinaryField('logo', blank=True, null=True)
    # "Beyond Your Neighborhood" 
    cover_image = CloudinaryField('cover_image', blank=True, null=True)
    
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    delivery_fee = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    delivery_time_minutes = models.PositiveIntegerField(default=30)
    distance_miles = models.DecimalField(max_digits=5, decimal_places=1, default=1.0)
    is_beyond_neighborhood = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    allows_delivery = models.BooleanField(default=True, help_text="support delivery or not")
    has_offers = models.BooleanField(default=False)
    shop_title = models.CharField(max_length=100 , null= True , blank=True)
    shop_address = models.CharField(
        max_length=255, null=True, blank=True, help_text="give address"
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    offers = models.CharField(max_length=200 , default="write offer")
    deal_validity = models.DateTimeField(default=timezone.now)
    redemption_type=models.CharField(max_length=30 , choices=Redemption_CHOICES , default="delivery & pickup")
    is_favourite=models.BooleanField(default=False)
    min_order=models.IntegerField(default=00)



    def save(self, *args, **kwargs):      
        if self.shop_address:
            geolocator = Nominatim(user_agent="qoupon_app_v1") 
            try:
                # fetch location from address 
                location = geolocator.geocode(self.shop_address, timeout=10)
                if location:
                    self.latitude = location.latitude
                    self.longitude = location.longitude
                
            except (GeocoderTimedOut, GeocoderUnavailable) as e:
                print(f"Error: Geocoding service timed out for address '{self.shop_address}'. Error: {e}")
            except Exception as e:
                print(f"An unexpected error occurred during geocoding: {e}")
        super().save(*args, **kwargs)
  
    
  
    PRICE_CHOICES = (
        (1, 'start'),
        (2, 'medium'),
        (3, 'high'),
    )
    price_range = models.IntegerField(choices=PRICE_CHOICES, default=1)
    
    def __str__(self):
        return self.name



# Vendor site 
class BusinessHours(models.Model):
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, 'Monday'
        TUESDAY = 1, 'Tuesday'
        WEDNESDAY = 2, 'Wednesday'
        THURSDAY = 3, 'Thursday'
        FRIDAY = 4, 'Friday'
        SATURDAY = 5, 'Saturday'
        SUNDAY = 6, 'Sunday'
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user', null= True )
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='business_hours')
    day = models.IntegerField(choices=DayOfWeek.choices)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    

    is_closed = models.BooleanField(default=False, help_text="Is this closed Shop full day ")

    class Meta:
        unique_together = ('shop', 'day')

    def __str__(self):
        return f"{self.shop.name} - {self.get_day_display()}"
































class SearchQuery(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    query_text = models.CharField(max_length=255)
    search_count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.query_text