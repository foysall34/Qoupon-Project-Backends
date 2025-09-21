import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import QRCode
from .serializers import QRCodeSerializer


class GenerateQRCodeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data.get("data")
        if not data:
            return Response({"error": "data field is required"}, status=400)

        # Generate QR code
        qr = qrcode.make(data)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        file_name = f"qr_{request.user.id}_{QRCode.objects.count()+1}.png"

        # Save QR code to model
        qr_code = QRCode(user=request.user, data=data)
        qr_code.image.save(file_name, ContentFile(buffer.getvalue()), save=True)

        serializer = QRCodeSerializer(qr_code)
        return Response(serializer.data, status=201)
    
    def get(self, request):
        user_qrs = QRCode.objects.filter(user=request.user)
        serializer = QRCodeSerializer(user_qrs, many=True)
        return Response(serializer.data)
