
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import categoryItemListView,DealViewSet, CategoryViewSet, ModifierGroupViewSet , CreateStoreView ,CreateDealListCreateView,CreateDealDetailView


router = DefaultRouter()
router.register(r'deals', DealViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'modifier-groups', ModifierGroupViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('business-profile/', CreateStoreView.as_view(), name='create-store'),
    path('create-deals/', CreateDealListCreateView.as_view(), name='deal-list-create'),
    path('create-deals/<int:pk>/', CreateDealDetailView.as_view(), name='deal-detail'),
    path('mymenu-category/', categoryItemListView.as_view(), name='menu-item-list'),
]