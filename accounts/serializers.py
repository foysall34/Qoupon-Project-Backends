from rest_framework import serializers
from .models import User
from django.utils import timezone
from datetime import timedelta

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'user_type', 'referral_code']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class SetNewPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)
    password = serializers.CharField(write_only=True)