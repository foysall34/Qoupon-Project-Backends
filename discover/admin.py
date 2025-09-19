from django.contrib import admin
# from .models import
from .models import  MenuItem, MenuCategory,CartItem, Cart,OptionGroup, OptionChoice, Cart,CartItem, Restaurant, Cuisine , Diet, Offer, CoffeeSubscriptionOffer , Order ,  VendorFollowed, ReviewMenuItem, FAQ


admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(OptionGroup)
admin.site.register(OptionChoice)
admin.site.register(MenuCategory)
# admin.site.register(MenuItem)
admin.site.register(VendorFollowed)
admin.site.register(Order)
admin.site.register(Restaurant)
admin.site.register(Cuisine)
admin.site.register(Diet)
admin.site.register(Offer)
admin.site.register(CoffeeSubscriptionOffer)
# Register your models here.

class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "name", "description", "price", "calories", "image", "added_to_cart")
    # list_filter = ('category', 'is_available')
    search_fields = ('name', 'description')
admin.site.register(MenuItem, MenuItemAdmin)



class ReviewMenuItemAdmin(admin.ModelAdmin):
    list_display = ("id", "menu_item", "user", "rating", "comment", "created_at")
    list_filter = ('rating', 'created_at')
    search_fields = ('menu_item__name', 'user__username', 'comment')
admin.site.register(ReviewMenuItem, ReviewMenuItemAdmin)


class FAQAdmin(admin.ModelAdmin):    
    list_display = ("id", "question", "answer")
    search_fields = ('question', 'answer')
admin.site.register(FAQ, FAQAdmin)