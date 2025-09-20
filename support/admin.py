from django.contrib import admin

from support.models import FAQ, IssueType, ReportIssue

# Register your models here.
class FAQAdmin(admin.ModelAdmin):    
    list_display = ("id", "question", "answer", "is_active")
    search_fields = ('question', 'answer')
admin.site.register(FAQ, FAQAdmin)


class IssueTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "is_active")
    search_fields = ('name', 'description')
admin.site.register(IssueType, IssueTypeAdmin)


class ReportIssueAdmin(admin.ModelAdmin):
    list_display = ("id", "reporter", "issue_type", "description", "created_at", "updated_at")
    list_filter = ('issue_type', 'created_at')
    search_fields = ('reporter__username', 'description')
admin.site.register(ReportIssue, ReportIssueAdmin)