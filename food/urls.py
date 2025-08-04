from django.urls import path
from .views import food_category_list, create_user_profile , get_user_profile , place_detail , place_list

urlpatterns = [
    
    path('food-categories/', food_category_list, name='food-category-list'),
    path('profiles/', create_user_profile, name='create-user-profile'),
    path('profiles/<str:email>/', get_user_profile, name='get-user-profile'),

        # /api/places/ - GET (list), POST (create)
    path('places/', place_list, name='place-list'),
    
    # /api/places/<id>/ - GET (detail), PUT/PATCH (update), DELETE (delete)
    path('places/<int:pk>/', place_detail, name='place-detail'),
]