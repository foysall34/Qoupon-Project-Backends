# your_app/urls.py

from django.urls import path
from .views import (
    CategoryListView,
    BeyondNeighborhoodView,
    RecentSearchView,
    FrequentSearchView,
    ShopFilterView,
)

urlpatterns = [
    # ১. সব ক্যাটাগরি দেখার জন্য: /api/categories/
    path('categories/', CategoryListView.as_view(), name='category-list'),

    # ২. শপ সার্চ এবং ক্যাটাগরি ফিল্টারের জন্য:
    # /api/shops/search/?q=pizza
    # /api/shops/search/?category=2
    path('shops/search/', ShopFilterView.as_view(), name='shop-search'),

    # ৩. "Beyond Your Neighborhood" শপগুলো দেখার জন্য: /api/shops/beyond-neighborhood/
    path('shops/beyond-neighborhood/', BeyondNeighborhoodView.as_view(), name='beyond-neighborhood-list'),

    # ৪. সাম্প্রতিক সার্চ দেখার জন্য: /api/search/recent/
    path('search/recent/', RecentSearchView.as_view(), name='recent-searches'),

    # ৫. জনপ্রিয় সার্চ দেখার জন্য: /api/search/frequent/
    path('search/frequent/', FrequentSearchView.as_view(), name='frequent-searches'),
]