from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('accounts.urls')), 
    path('food/', include('food.urls')), 
    path('home/' , include('homepage.urls')),
    path('discover/' , include('discover.urls')),
    path('vendors/' ,  include('vendors.urls')),
    path('support/' ,  include('support.urls'))
]