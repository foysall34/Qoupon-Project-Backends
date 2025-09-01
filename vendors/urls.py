
from django.urls import path
from .views import CreateStoreView

urlpatterns = [
    path('business-profile/', CreateStoreView.as_view(), name='create-store'),
]