from django.urls import path
from .views import RestaurantListView , OfferDetailView , FavoriteOffersListView , FavoriteToggleView

urlpatterns = [
    path('list/', RestaurantListView.as_view(), name='restaurant-list'),
    
    path('offers/<int:pk>/', OfferDetailView.as_view(), name='offer-detail'),
    path('offers/<int:pk>/favorite/', FavoriteToggleView.as_view(), name='offer-favorite-toggle'),
    path('favorites/', FavoriteOffersListView.as_view(), name='favorite-offers-list'),
]