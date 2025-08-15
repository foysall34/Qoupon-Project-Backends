from django.contrib import admin
from .models import Restaurant, Cuisine , Diet, Offer, CoffeeSubscriptionOffer


admin.site.register(Restaurant)
admin.site.register(Cuisine)
admin.site.register(Diet)
admin.site.register(Offer)
admin.site.register(CoffeeSubscriptionOffer)
# Register your models here.
