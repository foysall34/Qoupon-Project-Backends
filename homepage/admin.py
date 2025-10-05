from django.contrib import admin
from .models import Category
from .models import Shop 
from .models import SearchQuery, BusinessHours

admin.site.register(Category)
admin.site.register(Shop)
admin.site.register(SearchQuery)
# admin.site.register(BusinessHours)
# Register your models here.

class BusinessHoursAdmin(admin.ModelAdmin):
    list_display = ('user', 'day', 'open_time', 'close_time', 'is_closed')
    list_filter = ('user', 'day', 'is_closed')
    search_fields = ('user__username',)
admin.site.register(BusinessHours, BusinessHoursAdmin)