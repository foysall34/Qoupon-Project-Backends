from django.urls import path
from . import views
 
urlpatterns = [
    # Cart URLs
    path('cart/', views.get_cart, name='cart-detail'),
    path('cart/add/', views.add_to_cart, name='add-to-cart'),
    path('cart/item/<int:item_id>/', views.update_cart_item, name='update-cart-item'),
    path('cart/item/<int:item_id>/delete/', views.delete_cart_item, name='delete-cart-item'),
    path('cart/item/<int:item_id>/increment/', views.increment_cart_item, name='increment-cart-item'),
    path('cart/item/<int:item_id>/decrement/', views.decrement_cart_item, name='decrement-cart-item'),
    path('cart/clear/', views.clear_cart, name='clear-cart'),
    path('cart/checkout/calculate/', views.calculate_checkout, name='calculate-checkout'),
    
    # Order URLs
    path('orders/', views.order_list, name='order-list'),
    path('orders/<uuid:order_id>/', views.order_detail, name='order-detail'),
    path('orders/create/', views.create_order, name='create-order'),
    path('orders/<uuid:order_id>/cancel/', views.cancel_order, name='cancel-order'),
    path('orders/<uuid:order_id>/tracking/', views.order_tracking, name='order-tracking'),
    path('orders/<uuid:order_id>/process-payment/', views.process_payment, name='process-payment'),
    path('orders/<uuid:order_id>/delivery-qr/', views.get_delivery_qr, name='delivery-qr'),
    path('orders/<uuid:order_id>/verify-delivery/', views.verify_delivery, name='verify-delivery'),
    path('orders/<uuid:order_id>/status/', views.update_order_status, name='update-order-status'),
    
    path('webhook/mollie/', views.mollie_webhook, name='mollie-webhook'),
]