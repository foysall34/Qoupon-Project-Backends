
from django.urls import path
from .views import (
    CategoryListView,
    BeyondNeighborhoodView,
    RecentSearchView,
    FrequentSearchView,
    ShopFilterView,
)

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
]