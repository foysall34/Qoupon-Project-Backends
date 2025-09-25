from django.urls import path
from . import views

urlpatterns = [
    path('device/register/', views.register_device, name='register-device'),
    path('device/unregister/', views.unregister_device, name='unregister-device'),
    path('list/', views.get_notifications, name='get-notifications'),
    path('mark-read/<int:notification_id>/', views.mark_notification_read, name='mark-notification-read'),
    path('mark-all-read/', views.mark_all_notifications_read, name='mark-all-notifications-read'),
    path('test/', views.test_notification, name='test-notification'),
]