from django.contrib import admin

# Register your models here.
from .models import Business_profile, Business_profile_Category
admin.site.register(Business_profile)
admin.site.register(Business_profile_Category)