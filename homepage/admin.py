from django.contrib import admin
from .models import Category
from .models import Shop 
from .models import SearchQuery

admin.site.register(Category)
admin.site.register(Shop)
admin.site.register(SearchQuery)
# admin.site.register(BusinessHours)
# Register your models here.
