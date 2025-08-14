from django.urls import path
from .views import RestaurantListView

urlpatterns = [
    path('list/', RestaurantListView.as_view(), name='restaurant-list'),
    path('list/', RestaurantListView.as_view(), name='restaurant-list'),
]