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
    category = models.ForeignKey(Business_profile_Category, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name