# support/models.py
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


# class HelpCenterCategory(models.Model):
#     name = models.CharField(max_length=120, unique=True)
#     blurb = models.CharField(max_length=200, blank=True)  # short description for tile

#     def __str__(self):
#         return self.name


class FAQ(models.Model):
    # category = models.ForeignKey(HelpCenterCategory, related_name="faqs", on_delete=models.CASCADE, blank=True, null=True)
    question = models.CharField(max_length=255)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.question


# models.py
class IssueType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ReportIssue(models.Model):
    reporter = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="reported_issues"
    )
    issue_type = models.ForeignKey(IssueType, on_delete=models.PROTECT, related_name="issues")
    description = models.TextField()
    screenshot = models.ImageField(upload_to="support/screenshots/%Y/%m/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        who = getattr(self.reporter, "username", "Guest")
        return f"{self.issue_type} • {who}"
