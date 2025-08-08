from django.urls import path
from .views import (
    UserRegistrationView,
    VerifyOTPView,
    ForgotPasswordView,
    SetNewPasswordView,
    CustomLoginView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Authentication APIs
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    
    # Login API (using simple-jwt)
    path('login/', CustomLoginView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Password Reset APIs
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('set-new-password/', SetNewPasswordView.as_view(), name='set-new-password'),
]