
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BusinessProfileCategoryViewSet,categoryItemListView,DealViewSet, CategoryViewSet, ModifierGroupViewSet , CreateStoreView ,CreateDealViewSet


router = DefaultRouter()
router.register(r'deals', DealViewSet , basename='deal')
router.register(r'create-deals', CreateDealViewSet, basename='create-deal')
router.register(r'categories', CategoryViewSet)
router.register(r'modifier-groups', ModifierGroupViewSet)
router.register(r'vendor-categories', BusinessProfileCategoryViewSet, basename='business-profile-category')


urlpatterns = [
    path('', include(router.urls)),
    path('business-profile/', CreateStoreView.as_view(), name='create-store'),
    path('mymenu-category/', categoryItemListView.as_view(), name='menu-item-list'),

]