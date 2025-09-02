
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DealViewSet, CategoryViewSet, ModifierGroupViewSet , CreateStoreView

# Create a router to automatically generate URLs for our ViewSets.
router = DefaultRouter()
router.register(r'deals', DealViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'modifier-groups', ModifierGroupViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
    path('business-profile/', CreateStoreView.as_view(), name='create-store'),
]