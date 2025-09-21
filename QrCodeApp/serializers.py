from rest_framework import serializers
from .models import UserQR

class UserQRSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    qr_image_url = serializers.SerializerMethodField()

    class Meta:
        model = UserQR
        fields = [
            "id",
            "user_id",
            "url",
            "qr_image_url",
            "created_at",
        ]

    def get_qr_image_url(self, obj):
        try:
            return obj.qr_image.url if obj.qr_image else None
        except Exception:
            return None
