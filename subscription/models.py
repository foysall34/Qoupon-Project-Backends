from django.db import models
from django.conf import settings
from django.utils import timezone


class SubscriptionPlan(models.Model):
    """Plans available for subscription"""
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR")
    interval = models.CharField(
        max_length=20,
        choices=[
            ("1 month", "Monthly"),
            ("1 year", "Yearly"),
        ],
        default="1 month"
    )
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.amount} {self.currency}/{self.interval})"


class Subscription(models.Model):
    """User subscription linked to Mollie subscription"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    mollie_customer_id = models.CharField(max_length=100)
    mollie_subscription_id = models.CharField(max_length=100)
    status = models.CharField(max_length=30, default="pending")  # active, canceled, pending
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    cancel_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} -> {self.plan} ({self.status})"
    
    @property
    def is_active(self):
        """
        Returns True if subscription is currently active.
        """
        if self.status != "active":
            return False
        if self.end_date and self.end_date <= timezone.now():
            return False
        return True