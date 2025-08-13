
from django.urls import path
from .views import (
    CategoryListView,
    BeyondNeighborhoodView,
    RecentSearchView,
    FrequentSearchView,
    ShopFilterView,
)
from .views import BusinessHoursView 
urlpatterns = [

    path('categories/', CategoryListView.as_view(), name='category-list'),
    # ২. শপ সার্চ এবং ক্যাটাগরি ফিল্টারের জন্য:
    # /api/shops/search/?q=pizza
    # /api/shops/search/?category=2
    path('shops/search/', ShopFilterView.as_view(), name='shop-search'),

    # ৩. "Beyond Your Neighborhood" শপগুলো দেখার জন্য: /api/shops/beyond-neighborhood/
    path('shops/beyond-neighborhood/', BeyondNeighborhoodView.as_view(), name='beyond-neighborhood-list'),

    path('search/recent/', RecentSearchView.as_view(), name='recent-searches'),

    path('search/frequent/', FrequentSearchView.as_view(), name='frequent-searches'),

    path('shops/near-you/', ShopFilterView.as_view(), name='shops-near-you'),
    path('shops/<int:shop_id>/business-hours/', BusinessHoursView.as_view(), name='shop-business-hours'),
]