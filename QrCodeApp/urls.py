from django.urls import path
from .views import GenerateQRView

urlpatterns = [
    path("generate/", GenerateQRView.as_view(), name="generate-qr-code"),
]
