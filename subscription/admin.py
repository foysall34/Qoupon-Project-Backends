from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import SubscriptionPlan, Subscription

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'formatted_amount', 'interval', 'currency')
    list_filter = ('interval', 'currency')
    search_fields = ('name', 'description')
    ordering = ('amount', 'name')

    def formatted_amount(self, obj):
        return f"{obj.amount} {obj.currency}"
    formatted_amount.short_description = 'Price'

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'plan_name', 'status', 'subscription_period', 'is_active_status', 'mollie_link')
    list_filter = ('status', 'plan', 'start_date')
    search_fields = ('user__email', 'mollie_customer_id', 'mollie_subscription_id')
    readonly_fields = ('start_date', 'cancel_date', 'mollie_customer_id', 'mollie_subscription_id')
    raw_id_fields = ('user',)
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)

    fieldsets = (
        ('Subscription Information', {
            'fields': ('user', 'plan', 'status')
        }),
        ('Period', {
            'fields': ('start_date', 'end_date', 'cancel_date')
        }),
        ('Mollie Details', {
            'fields': ('mollie_customer_id', 'mollie_subscription_id'),
            'classes': ('collapse',)
        })
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    
    def plan_name(self, obj):
        return obj.plan.name
    plan_name.short_description = 'Plan'
    
    def subscription_period(self, obj):
        if obj.end_date:
            return f"{obj.start_date.date()} to {obj.end_date.date()}"
        return f"From {obj.start_date.date()}"
    subscription_period.short_description = 'Period'

    def is_active_status(self, obj):
        is_active = obj.is_active
        if is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">●</span> Active'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">●</span> Inactive'
        )
    is_active_status.short_description = 'Active'

    def mollie_link(self, obj):
        if obj.mollie_subscription_id:
            return format_html(
                '<a href="https://www.mollie.com/dashboard/subscriptions/{}" target="_blank">'
                '<img src="https://www.mollie.com/favicon.ico" width="16" height="16" '
                'style="vertical-align: middle;"> View in Mollie</a>',
                obj.mollie_subscription_id
            )
        return '-'
    mollie_link.short_description = 'Mollie'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'plan')

    def save_model(self, request, obj, form, change):
        if not change and not obj.start_date:  # Only for new subscriptions
            obj.start_date = timezone.now()
        super().save_model(request, obj, form, change)
