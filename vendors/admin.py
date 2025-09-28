from django.contrib import admin

# Register your models here.
from .models import Business_profile, Business_profile_Category, Deal, Vendor_Category,ModifierGroup, Create_Deal,DeliveryCost, WishDeal


class BusinessProfileCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category_image')
    search_fields = ('name',)
    ordering = ('name',)
admin.site.register(Business_profile_Category, BusinessProfileCategoryAdmin)

class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'name', 'kvk_number', 'phone_number', 'address', 'category', 'created_at')
    search_fields = ('name', 'owner__email', 'kvk_number')
    list_filter = ('category', 'created_at')
    ordering = ('-created_at',)
admin.site.register(Business_profile, BusinessProfileAdmin)

class DealAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'discount_value', 'user', 'created_at')
    search_fields = ('title', 'user__email')
    list_filter = ('created_at',)
    ordering = ('-created_at',)

admin.site.register(Create_Deal, DealAdmin)

class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'description', 'price', 'category', 'created_at')
    search_fields = ('title', 'user__email')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
admin.site.register(Deal, MenuItemAdmin)


class DeliveryCostAdmin(admin.ModelAdmin):
    list_display = ('id', 'deal', 'zip_code', 'delivery_fee', 'min_order_amount')
    search_fields = ('location',)
    # ordering = ('location',)
admin.site.register(DeliveryCost, DeliveryCostAdmin)


class VendorCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category_title', 'choice_category', 'category_price')
    search_fields = ('category_title', 'choice_category')
    list_filter = ('choice_category',)
    ordering = ('category_title',)
admin.site.register(Vendor_Category, VendorCategoryAdmin) 


class ModifierGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('name',)
admin.site.register(ModifierGroup, ModifierGroupAdmin)


class WishDealAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'deal', 'added_at')
    search_fields = ('user__email', 'deal__title')
    list_filter = ('added_at',)
    ordering = ('-added_at',)
admin.site.register(WishDeal, WishDealAdmin)


# admin.site.register(Create_Deal)
# admin.site.register(DeliveryCost)
# admin.site.register(Deal)
# admin.site.register(Vendor_Category)
# admin.site.register(ModifierGroup)
# admin.site.register(Business_profile)
# admin.site.register(Business_profile_Category)
# admin.site.register(WishDeal)