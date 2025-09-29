from django.contrib import admin

# Register your models here.
from .models import Business_profile, Business_profile_Category, Deal, Vendor_Category,ModifierGroup, Create_Deal,DeliveryCost, WishDeal, DealTimeSlot, Create_Deal, DealTimeSlot


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

# class DealAdmin(admin.ModelAdmin):
#     list_display = ('id', 'title', 'discount_value', 'user', 'created_at')
#     search_fields = ('title', 'user__email')
#     list_filter = ('created_at',)
#     ordering = ('-created_at',)

# admin.site.register(Create_Deal, DealAdmin)

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

'''
class DealTimeSlotInline(admin.TabularInline):
    model = DealTimeSlot
    extra = 1  
    fields = ['day', 'is_active', 'start_time', 'end_time'] 

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.order_by('day') 
    
    

class DealAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'discount_value_free','discount_value_paid', 'user', 'created_at')
    search_fields = ('title', 'user__email')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    inlines = [DealTimeSlotInline]

admin.site.register(Create_Deal, DealAdmin)

'''


from django.contrib import admin
from .models import DealTimeSlot, Create_Deal

class DealTimeSlotInline(admin.TabularInline):
    model = DealTimeSlot
    extra = 1  
    fields = ['day', 'is_active', 'start_time', 'end_time']

    # Customizing the queryset to filter by 'day' or 'is_active'
    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        # Example: filter by active status
        is_active = request.GET.get('is_active')  # Example of checking a GET parameter for 'is_active'
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)

        # Example: filter by day, could also use a parameter in request if you need dynamic filtering
        day_filter = request.GET.get('day')
        if day_filter:
            queryset = queryset.filter(day=day_filter)

        return queryset.order_by('day')  # Optionally, sort by day

    # Optional: Add a custom filter for 'day' or 'is_active'
    def day_filter(self, request):
        # Dynamically add filter options to the inline form (e.g., by day)
        # You can use a drop-down filter for days or status, for example
        return DealTimeSlot.objects.values_list('day', flat=True).distinct()
        
    # Optional: You could also implement filters for more fields if needed
    def is_active_filter(self, request):
        return DealTimeSlot.objects.values_list('is_active', flat=True).distinct()


class DealAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'discount_value_free', 'user', 'created_at')
    search_fields = ('title', 'user__email')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    inlines = [DealTimeSlotInline]

admin.site.register(Create_Deal, DealAdmin)

@admin.register(DealTimeSlot)
class DealTimeSlotAdmin(admin.ModelAdmin):
    list_display = ('deal', 'day', 'is_active', 'start_time', 'end_time')
    list_filter = ('day', 'is_active')  
    search_fields = ('deal__title', 'day')  
    ordering = ('deal', 'day')




# admin.site.register(Create_Deal)
# admin.site.register(DeliveryCost)
# admin.site.register(Deal)
# admin.site.register(Vendor_Category)
# admin.site.register(ModifierGroup)
# admin.site.register(Business_profile)
# admin.site.register(Business_profile_Category)
# admin.site.register(WishDeal)