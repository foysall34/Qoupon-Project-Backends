from django.urls import path
from .views import food_category_list, manage_my_favorite_categories  ,user_profile_view , place_detail , place_list

urlpatterns = [
    
    path('food-categories/', food_category_list, name='food-category-list'),
    path('user-fvt-categories/', manage_my_favorite_categories, name='create-user-profile'),
    path('my-profile/', user_profile_view , name = 'my-profile'),
    path('places/', place_list, name='place-list'),
    path('places/<int:pk>/', place_detail, name='place-detail'),
]