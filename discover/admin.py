from django.contrib import admin
from .models import CartItem, Cart,OptionGroup, OptionChoice, Cart,CartItem,Restaurant, Cuisine , Diet, Offer, CoffeeSubscriptionOffer , Order ,  VendorFollowed , MenuItem, MenuCategory



admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(OptionGroup)
admin.site.register(OptionChoice)
admin.site.register(MenuCategory)
admin.site.register(MenuItem)
admin.site.register(VendorFollowed)
admin.site.register(Order)
admin.site.register(Restaurant)
admin.site.register(Cuisine)
admin.site.register(Diet)
admin.site.register(Offer)
admin.site.register(CoffeeSubscriptionOffer)
# Register your models here.
