from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField

class UserQR(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="user_qrs")
    order_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    url = models.URLField()
    qr_image = CloudinaryField("qrcode")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"QR for {self.user} - {self.url}"
