from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class QRCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="user_qrs")
    data = models.TextField()  # The text/URL encoded
    image = models.ImageField(upload_to="qrcodes/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"QR Code for {self.user} - {self.data[:20]}"
