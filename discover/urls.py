from django.urls import path
from .views import  MenuCategoryListAPIView,VendorSearchListView, OrderListView,RestaurantListView , OfferDetailView , FavoriteOffersListView , FavoriteToggleView , PretCoffeeSubscriptionAPIView

urlpatterns = [
    path('list/', RestaurantListView.as_view(), name='restaurant-list'),
    
    path('offers/<int:pk>/', OfferDetailView.as_view(), name='offer-detail'),
    path('offers/<int:pk>/favorite/', FavoriteToggleView.as_view(), name='offer-favorite-toggle'),
    path('favorites/', FavoriteOffersListView.as_view(), name='favorite-offers-list'),
    path('qr-scanner/', PretCoffeeSubscriptionAPIView.as_view(), name='pret_offer_api'),

    path('my-orders/', OrderListView.as_view(), name='my-order-list'),

    path('followed-vendors/', VendorSearchListView.as_view(), name='followed-vendor-list'),
    path('menu/', MenuCategoryListAPIView.as_view(), name='menu-list'),
        # /api/cart/ - কার্টের বিস্তারিত তথ্যের জন্য
    # path('cart/', CartDetailAPIView.as_view(), name='cart-detail-api'),
    
    # # /api/cart-items/ - আইটেমের তালিকা দেখা এবং নতুন আইটেম যোগ করা
    # path('cart-items/', CartItemListCreateAPIView.as_view(), name='cart-item-list-create-api'),
    
    # # /api/cart-items/<pk>/ - একটি নির্দিষ্ট আইটেম দেখা, আপডেট করা বা ডিলিট করা
    # path('cart-items/<int:pk>/', CartItemDetailAPIView.as_view(), name='cart-item-detail-api'),
    
]