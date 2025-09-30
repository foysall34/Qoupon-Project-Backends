
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import  CreateStoreViewPatch,AllBusinessProfilesListView,ImageUploadView,BusinessProfileCategoryViewSet,categoryItemListView,DealViewSet, CategoryViewSet, ModifierGroupViewSet , CreateStoreView ,CreateDealViewSet
from . import views


router = DefaultRouter()
router.register(r'deals', DealViewSet , basename='deal')
router.register(r'create-deals', CreateDealViewSet, basename='create-deal')
router.register(r'categories', CategoryViewSet)
router.register(r'modifier-groups', ModifierGroupViewSet)
router.register(r'vendor-categories', BusinessProfileCategoryViewSet, basename='business-profile-category')


urlpatterns = [
    path('', include(router.urls)),
    path('business-profile/', CreateStoreView.as_view(), name='create-store'),
    path('all-business-profile/', AllBusinessProfilesListView.as_view(), name='all-stores-list'),
    path('businessh-profile/manage/', CreateStoreViewPatch.as_view(), name='store-detail'),
    path('mymenu-category/', categoryItemListView.as_view(), name='menu-item-list'),
    path('upload/', ImageUploadView.as_view(), name='image-upload'),
    path('all-deals/', views.AllDealsView.as_view(), name='all-deals-list'),
    path('all-deals/<int:id>/', views.ALlDealsDetailsView.as_view(), name='all-deals-detail'),

    path('wish-deals/', views.WishDealListCreateView.as_view(), name='wish-deals-list-create'),
    path('wish-deals/<int:pk>/', views.WishDealListCreateView.as_view(), name='wish-deals-delete'),  # Add DELETE URL

    path('qr/deals/<int:id>/', views.DealByIDView.as_view(), name='deal'),
    path('vendor/<int:vendor_id>/deals/', views.VendorDealListView.as_view(), name='vendor-deals-list'),
    path('<int:deal_id>/send-notification/', views.SendDealNotification.as_view(), name='vendor-create-deals-list'),
    path('all-vendor-deals/', views.AllVendorDealsView.as_view(), name='all-vendor-deals-list'),

]       