
from django.urls import path
from .views import (
    CategoryListView,
    BeyondNeighborhoodView,
    RecentSearchView,
    FrequentSearchView,
    ShopFilterView,
    UserBusinessHoursAPIView
)

urlpatterns = [

    path('categories/', CategoryListView.as_view(), name='category-list'),

    path('shops/search/', ShopFilterView.as_view(), name='shop-search'),

    # ৩. "Beyond Your Neighborhood" শপগুলো দেখার জন্য: /api/shops/beyond-neighborhood/
    path('shops/beyond-neighborhood/', BeyondNeighborhoodView.as_view(), name='beyond-neighborhood-list'),

    path('search/recent/', RecentSearchView.as_view(), name='recent-searches'),

    path('search/frequent/', FrequentSearchView.as_view(), name='frequent-searches'),
   

    path('shops/near-you/', ShopFilterView.as_view(), name='shops-near-you'),
    path('users/<int:user_id>/business-hours/', UserBusinessHoursAPIView.as_view(), name='shop-business-hours'),
]