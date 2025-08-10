from django.urls import path
from .views import food_category_list, manage_my_favorite_categories  , place_detail , place_list

urlpatterns = [
    
    path('food-categories/', food_category_list, name='food-category-list'),
    path('user-fvt-categories/', manage_my_favorite_categories, name='create-user-profile'),
  

        # /api/places/ - GET (list), POST (create)
    path('places/', place_list, name='place-list'),
    
    # /api/places/<id>/ - GET (detail), PUT/PATCH (update), DELETE (delete)
    path('places/<int:pk>/', place_detail, name='place-detail'),
]