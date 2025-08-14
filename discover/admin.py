from django.contrib import admin
from .models import Restaurant, Cuisine , Diet, Offer


admin.site.register(Restaurant)
admin.site.register(Cuisine)
admin.site.register(Diet)
admin.site.register(Offer)

# Register your models here.
