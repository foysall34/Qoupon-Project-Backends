from django.urls import path
from .views import  CreatePaymentView,MenuCategoryDetailAPIView,MenuCategoryListAPIView,VendorSearchListView, OrderListView,RestaurantListView , OfferDetailView , FavoriteOffersListView , FavoriteToggleView , PretCoffeeSubscriptionAPIView
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()


router.register(r'cart-items', views.CartItemViewSet, basename='cart-item')



urlpatterns = [
    path('list/', RestaurantListView.as_view(), name='restaurant-list'),
    path('offers/<int:pk>/', OfferDetailView.as_view(), name='offer-detail'),
    path('offers/<int:pk>/favorite/', FavoriteToggleView.as_view(), name='offer-favorite-toggle'),
    path('favorites/', FavoriteOffersListView.as_view(), name='favorite-offers-list'),
    path('qr-scanner/', PretCoffeeSubscriptionAPIView.as_view(), name='pret_offer_api'),
    path('my-orders/', OrderListView.as_view(), name='my-order-list'),
    path('followed-vendors/', VendorSearchListView.as_view(), name='followed-vendor-list'),
    path('cart/',views.CartViewSet.as_view({'get': 'retrieve', 'patch': 'update', 'put': 'update'}),name='cart-detail' ),
    path('menu/<int:user_id>/name/', MenuCategoryListAPIView.as_view(), name='user-category-list'),
    
    path('menu/<int:user_id>/categories/<int:pk>/', MenuCategoryDetailAPIView.as_view(), name='user-category-detail'),
    path('payment/'  , CreatePaymentView.as_view() , name= 'mollie-payment'),
    path('', include(router.urls)),
    path('review-menu-item/', views.ReviewMenuItemViewSet.as_view({'post': 'create'}), name='review-menu-item-create'),
    path('faqs/', views.FAQListView.as_view(), name='faq-list'),
   
    
]








