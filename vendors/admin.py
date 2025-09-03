from django.contrib import admin

# Register your models here.
from .models import Business_profile, Business_profile_Category, Deal, Vendor_Category,ModifierGroup, Create_Deal,DeliveryCost


admin.site.register(Create_Deal)
admin.site.register(DeliveryCost)
admin.site.register(Deal)
admin.site.register(Vendor_Category)
admin.site.register(ModifierGroup)
admin.site.register(Business_profile)
admin.site.register(Business_profile_Category)