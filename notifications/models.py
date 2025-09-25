from django.db import models
from django.conf import settings

class FCMDevice(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fcm_devices')
    registration_id = models.TextField(verbose_name="Device Registration ID/Token")
    type = models.CharField(max_length=10, choices=[
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web')
    ])
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "FCM Device"
        verbose_name_plural = "FCM Devices"

    def __str__(self):
        return f"{self.user.email}'s {self.type} device"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('order_status', 'Order Status Update'),
        ('payment', 'Payment Update'),
        ('promotion', 'Promotional'),
        ('system', 'System Update'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    body = models.TextField()
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    data = models.JSONField(default=dict, blank=True)  # Additional data to be sent with notification
    read = models.BooleanField(default=False)
    sent = models.BooleanField(default=False)
    error = models.TextField(blank=True, null=True)  # Store any sending errors
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.email}"
