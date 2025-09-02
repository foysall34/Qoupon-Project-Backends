# stores/models.py

from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField

class Business_profile_Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class Business_profile(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shops')
    name = models.CharField(max_length=255, verbose_name="Store Name")
    logo = CloudinaryField('logo', null=True, blank=True)
    kvk_number = models.CharField(max_length=50, unique=True, verbose_name="KVK Number")
    phone_number = models.CharField(max_length=20, verbose_name="Phone Number")
    address = models.TextField(verbose_name="Store Address")
    category = models.ForeignKey(Business_profile_Category, on_delete=models.CASCADE )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

class Vendor_Category(models.Model):
    """
    Represents a category for a deal, e.g., "Breakfast", "Lunch".
    """
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class ModifierGroup(models.Model):
    """
    Represents a group of choices for a deal, e.g., "Choice of Toppings".
    """
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Deal(models.Model):
    """
    The main model representing the deal shown in the UI.
    """
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)

    image = CloudinaryField('logo', default = 'logo.jpg')
    category = models.ForeignKey(Vendor_Category, related_name='deals', on_delete=models.SET_NULL, null=True)
    modifier_groups = models.ManyToManyField(ModifierGroup, related_name='deals')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title