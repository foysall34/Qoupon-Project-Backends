from django.urls import path
# from .views import GenerateQRView
from . import views

urlpatterns = [
    path("generate/", views.GenerateQRCodeView.as_view(), name="generate_qr"),
]
