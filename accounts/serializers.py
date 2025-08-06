from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)


    class Meta:
        model = User
        fields = ['email', 'referral_code', 'password',  'user_type']

   

class CustomLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError({"error": "Invalid credentials."})

        if not user.is_active:
            raise serializers.ValidationError({"error": "User account is disabled."})

        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user_type": user.user_type,
             "user_email" : user.email , 
            "message": "Login successful"
        }



# forgot password 
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # ইমেলটি ডাটাবেজে আছে কিনা তা পরীক্ষা করা হচ্ছে
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4, min_length=4)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        # পাসওয়ার্ড দুটি মিলছে কিনা তা পরীক্ষা করা হচ্ছে
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        
        # ইমেলটি ডাটাবেজে আছে কিনা তা পরীক্ষা করা হচ্ছে
        if not User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("User with this email does not exist.")
            
        return data