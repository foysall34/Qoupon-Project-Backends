from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField
from django.db.models.signals import post_save
from django.dispatch import receiver


class FoodCategory(models.Model):
    name = models.CharField(max_length=100 , unique=True)
    emoji = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.name
    
class Fvt_category(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL , on_delete=models.CASCADE ,related_name='fvt_profile' )
    favorite_categories = models.ManyToManyField(FoodCategory, blank=True)

    def __str__(self):
        return self.user.get_username()
    

    # Google Map ingregation 
class Place(models.Model):
    name = models.CharField(max_length=255)
    # this field is fill up automatically 
    address = models.TextField(unique=True, help_text="must be unique")
    
    # এই দুটি ফিল্ড স্বয়ংক্রিয়ভাবে পূরণ হবে
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    





class Profile(models.Model): 
    LANGUAGE_CHOICES = (
        ('English', 'English'),
        ('Bengali', 'Bengali'),
        ('Spanish', 'Spanish'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')    
    # CloudinaryField 
    profile_picture = CloudinaryField('image', blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')

    def __str__(self):
         return f"{self.user.get_username()}'s Profile"

# সিগন্যাল: যখনই একজন নতুন User তৈরি হবে, তার জন্য একটি Profile অবজেক্টও স্বয়ংক্রিয়ভাবে তৈরি হয়ে যাবে
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()

