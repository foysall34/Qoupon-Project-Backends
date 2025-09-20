from django.contrib import admin

from support.models import FAQ

# Register your models here.
class FAQAdmin(admin.ModelAdmin):    
    list_display = ("id", "question", "answer")
    search_fields = ('question', 'answer')
admin.site.register(FAQ, FAQAdmin)