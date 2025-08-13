
from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = CloudinaryField('image', blank=True, null=True)

    def __str__(self):
        return self.name

class Shop(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, related_name='shops', on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True, null=True)
    
    # "Shops Near You" সেকশনের ছোট লোগোর জন্য
    logo = CloudinaryField('logo', blank=True, null=True)
    # "Beyond Your Neighborhood" সেকশনের বড় ছবির জন্য
    cover_image = CloudinaryField('cover_image', blank=True, null=True)
    
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    delivery_fee = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    delivery_time_minutes = models.PositiveIntegerField(default=30)
    distance_miles = models.DecimalField(max_digits=5, decimal_places=1, default=1.0)
    is_beyond_neighborhood = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    allows_pickup = models.BooleanField(default=False)
    has_offers = models.BooleanField(default=False)
    shop_title = models.CharField(max_length=100 , null= True , blank=True)
  
    
  
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

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='business_hours')
    day = models.IntegerField(choices=DayOfWeek.choices)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    

    is_closed = models.BooleanField(default=False, help_text="এই দিনে কি শপটি পুরোপুরি বন্ধ থাকবে?")

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