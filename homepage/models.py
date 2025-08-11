
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



    allows_pickup = models.BooleanField(default=False)
    
    # শপে কোনো অফার আছে কি না তার জন্য
    has_offers = models.BooleanField(default=False)

    PRICE_CHOICES = (
        (1, '$'),
        (2, '$$'),
        (3, '$$$'),
    )
    price_range = models.IntegerField(choices=PRICE_CHOICES, default=1)
    
    def __str__(self):
        return self.name

class SearchQuery(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    query_text = models.CharField(max_length=255)
    search_count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.query_text