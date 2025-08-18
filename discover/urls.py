from django.urls import path
from .views import MenuView,VendorSearchListView, OrderListView,RestaurantListView , OfferDetailView , FavoriteOffersListView , FavoriteToggleView , PretCoffeeSubscriptionAPIView

urlpatterns = [
    path('list/', RestaurantListView.as_view(), name='restaurant-list'),
    
    path('offers/<int:pk>/', OfferDetailView.as_view(), name='offer-detail'),
    path('offers/<int:pk>/favorite/', FavoriteToggleView.as_view(), name='offer-favorite-toggle'),
    path('favorites/', FavoriteOffersListView.as_view(), name='favorite-offers-list'),
    path('qr-scanner/', PretCoffeeSubscriptionAPIView.as_view(), name='pret_offer_api'),

    path('my-orders/', OrderListView.as_view(), name='my-order-list'),

    path('followed-vendors/', VendorSearchListView.as_view(), name='followed-vendor-list'),
    path('menu/', MenuView.as_view(), name='menu-list'),
    
]