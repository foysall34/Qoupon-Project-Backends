from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    UserRegistrationSerializer, 
    VerifyOTPSerializer,
    ForgotPasswordSerializer,
    SetNewPasswordSerializer,
    CustomTokenObtainPairSerializer
)
from .models import User
from .utils import generate_otp, send_otp_via_email
from django.utils import timezone
from datetime import timedelta




class CustomLoginView(TokenObtainPairView):
    
    serializer_class = CustomTokenObtainPairSerializer



# 1. Register API
class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # OTP generate
            otp = generate_otp()
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.save()
            
            # send otp to gmail 
            send_otp_via_email(user.email, otp)
            
            return Response({
                'message': 'Registration successful! Please check your email for OTP.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 2. Verify OTP API
class VerifyOTPView(APIView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

            # OTP is expired or not 
            if user.otp == otp and timezone.now() < user.otp_created_at + timedelta(minutes=10):
                user.is_active = True
                user.otp = None 
                user.otp_created_at = None
                user.save()
                return Response({'message': 'Account activated successfully!'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# 4. Forgot Password API
class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email, is_active=True)
            except User.DoesNotExist:
                return Response({'error': 'Active user with this email not found.'}, status=status.HTTP_404_NOT_FOUND)
            
            otp = generate_otp()
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.save()
            
            send_otp_via_email(user.email, otp)
            
            return Response({'message': 'OTP for password reset has been sent to your email.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 5. Set New Password API
class SetNewPasswordView(APIView):
    def post(self, request):
        serializer = SetNewPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            password = serializer.validated_data['password']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

            if user.otp == otp and timezone.now() < user.otp_created_at + timedelta(minutes=10):
                user.set_password(password)
                user.otp = None 
                user.otp_created_at = None
                user.save()
                return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)