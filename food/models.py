from django.db import models
from django.conf import settings
class FoodCategory(models.Model):
    name = models.CharField(max_length=100)
    emoji = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.name
    
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL , on_delete=models.CASCADE)
    favorite_categories = models.ManyToManyField(FoodCategory, blank=True)

    def __str__(self):
        return self.user.get_username()
    

    # Google Map ingregation 
class Place(models.Model):
    name = models.CharField(max_length=255)
    # ব্যবহারকারী শুধুমাত্র ঠিকানা দেবে
    address = models.TextField(unique=True, help_text="স্থানের সম্পূর্ণ ঠিকানা দিন, এটি ইউনিক হতে হবে।")
    
    # এই দুটি ফিল্ড স্বয়ংক্রিয়ভাবে পূরণ হবে
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name