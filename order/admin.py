from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, Cart, CartItem, CartDeal, AppliedDeal, OrderTracking

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('item_name', 'deal', 'quantity', 'unit_price', 'total_price', 'selected_modifiers', 'modifiers_price')
    can_delete = False
    max_num = 0
    
    def has_add_permission(self, request, obj=None):
        return False

class AppliedDealInline(admin.TabularInline):
    model = AppliedDeal
    extra = 0
    readonly_fields = ('deal', 'discount_amount', 'deal_title', 'deal_description')
    can_delete = False
    max_num = 0
    
    def has_add_permission(self, request, obj=None):
        return False

class OrderTrackingInline(admin.TabularInline):
    model = OrderTracking
    extra = 0
    readonly_fields = ('status', 'timestamp', 'note')
    can_delete = False
    max_num = 0
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user_email', 'status', 'payment_status', 'payment_method', 
                   'total_amount', 'delivery_type', 'created_at', 'qr_code_link')
    list_filter = ('status', 'payment_status', 'payment_method', 'delivery_type', 
                  'created_at', 'order_type')
    search_fields = ('order_id', 'user__email', 'delivery_address')
    readonly_fields = ('order_id', 'cart_snapshot', 'created_at', 'updated_at', 
                      'delivery_code', 'delivery_code_created_at', 'qr_code')
    inlines = [OrderItemInline, AppliedDealInline, OrderTrackingInline]
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'user', 'status', 'note')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'payment_status', 'payment_id')
        }),
        ('Amount Details', {
            'fields': ('subtotal', 'delivery_fee', 'discount_amount', 'total_amount')
        }),
        ('Delivery Information', {
            'fields': ('delivery_type', 'delivery_address', 
                      'delivery_address_latitude', 'delivery_address_longitude')
        }),
        ('Scheduling', {
            'fields': ('order_type', 'scheduled_datetime', 'estimated_delivery_time')
        }),
        ('Special Instructions', {
            'fields': ('special_instructions',)
        }),
        ('Delivery Verification', {
            'fields': ('delivery_code', 'delivery_code_created_at', 'delivery_code_used', 'qr_code')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'cart_snapshot'),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        return obj.user.email if obj.user else '-'
    user_email.short_description = 'Customer Email'

    def qr_code_link(self, obj):
        if obj.qr_code and obj.qr_code.image:
            return format_html('<a href="{}" target="_blank">View QR Code</a>', obj.qr_code.image.url)
        return '-'
    qr_code_link.short_description = 'QR Code'

@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'timestamp', 'note')
    list_filter = ('status', 'timestamp')
    search_fields = ('order__order_id', 'order__user__email')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
