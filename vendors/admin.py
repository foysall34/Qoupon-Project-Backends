from django.contrib import admin

# Register your models here.
from .models import Business_profile, Business_profile_Category, Deal, Vendor_Category,ModifierGroup
admin.site.register(Deal)
admin.site.register(Vendor_Category)
admin.site.register(ModifierGroup)
admin.site.register(Business_profile)
admin.site.register(Business_profile_Category)