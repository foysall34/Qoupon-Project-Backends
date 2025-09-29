
from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField
from notifications.utils import FirebaseNotification
from django.contrib.auth import get_user_model

User = get_user_model()

class Business_profile_Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category_image = CloudinaryField('logo' , null = True)
    
    def __str__(self):
        return self.name

class Business_profile(models.Model):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='business_profile')
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
    CATEGORY_CHOICES = [
        ('Breakfast', 'Breakfast'),
        ('Lunch', 'Lunch'),
        ('Dinner', 'Dinner'),
        ('Snacks', 'Snacks'),
    ]

    category_title = models.CharField(max_length=255 , default='write title')
    category_description = models.TextField(default='write description')
    category_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    category_image = CloudinaryField('logo' , null = True)
    choice_category = models.CharField(max_length=50, choices=CATEGORY_CHOICES , null= True )
                           
    

    def __str__(self):
        return f" {self.choice_category}"

class ModifierGroup(models.Model):
    
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# Product table 
class Deal(models.Model):
    """ 
     Menu part ******************
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deals_user' , null= True)
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
    
    class Meta:
        verbose_name = "Menu Item"
        verbose_name_plural = "Menu Items"
    

# create deals ---------------------------------------

# offer table

class Create_Deal(models.Model):
    class RedemptionType(models.TextChoices):
        DELIVERY = 'DELIVERY', 'Delivery'
        PICKUP = 'PICKUP', 'Pickup'
        # BOTH = 'BOTH', 'Delivery & Pickup'
    discount_percentage = {
        "0": "0",
        "5": "5",
        "10": "10",
        "25": "25",
        "50": "50",
        "1+1": "1+1",
        "FREE ITEM": "FREE ITEM",
        "PRE ORDER": "PRE ORDER",
        "LATE NIGHT": "LATE NIGHT",
        "QOUPON+": "QOUPON+"
    
    } 

    deal_type = {
        "Free": "Free",
        "Paid": "Paid",
        "Both": "Both"
    }

  
    linked_menu_item = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='deals')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='create', null= True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = CloudinaryField('deal_image')
    
    qrimage = models.ImageField(upload_to='deals_qr/', null=True, blank=True)
    # discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Percentage or fixed amount")
    discount_value_free = models.CharField(max_length=30, choices=discount_percentage, blank=True, null=True)
    discount_value_paid = models.CharField(max_length=30, choices=discount_percentage, blank=True, null=True)
    deal_type = models.CharField(max_length=20, choices=deal_type, null= True)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    redemption_type = models.CharField(max_length=20, choices=RedemptionType.choices)
    
    max_coupons_total = models.PositiveIntegerField(verbose_name="Max Coupons For This Deal")
    max_coupons_per_customer = models.PositiveIntegerField(default=1, verbose_name="Max Coupons Per Customer")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Vendor's Deal"
        verbose_name_plural = "Vendor's Deals"


class DealTimeSlot(models.Model):
    deal = models.ForeignKey(Create_Deal, on_delete=models.CASCADE)
    day = models.CharField(max_length=20, choices=[('Mon', 'Monday'), ('Tue', 'Tuesday'), ('Wed', 'Wednesday'), ('Thu', 'Thursday'), ('Fri', 'Friday'), ('Sat', 'Saturday'), ('Sun', 'Sunday')])
    is_active = models.BooleanField(default=False)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.deal.title} - {self.day} - Active: {self.is_active}"
    

    def filter_by_day(self, day):
        return DealTimeSlot.objects.filter(deal = self.deal)
        


class DeliveryCost(models.Model):
    deal = models.ForeignKey(Create_Deal, on_delete=models.CASCADE,related_name='delivery_costs')
    zip_code = models.CharField(max_length=20)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ('deal', 'zip_code') 

    def __str__(self):
        return f"{self.deal.title} - {self.zip_code}"
    



class Image(models.Model):
    image = CloudinaryField('image')


class WishDeal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wish_deals')
    deal = models.ForeignKey(Create_Deal, on_delete=models.CASCADE, related_name='wish_deals')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'deal')

    def __str__(self):
        return f"{self.user} - {self.deal.title}"