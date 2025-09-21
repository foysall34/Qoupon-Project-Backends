from io import BytesIO
from django.core.files.base import ContentFile
import qrcode
from qrcode.constants import ERROR_CORRECT_M

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import UserQR
from .serializers import UserQRSerializer


class GenerateQRView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Only validate the URL field
        url = request.data.get("url")
        if not url:
            return Response({"error": "URL is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Generate QR code
        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        # 2. Save QR image to buffer
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        buffer.seek(0)

        # 3. Create DB record (without image first)
        qr_obj = UserQR.objects.create(
            user=request.user,
            url=url,
        )

        # 4. Save image file to Cloudinary
        filename = f"user_{request.user.id}_{qr_obj.id}.png"
        qr_obj.qr_image.save(filename, ContentFile(buffer.read()), save=True)

        # 5. Return serialized response
        return Response(UserQRSerializer(qr_obj).data, status=status.HTTP_201_CREATED)
