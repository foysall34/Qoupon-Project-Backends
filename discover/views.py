from rest_framework.generics import ListAPIView
from django.http import Http404
from .models import Restaurant
from .serializers import RestaurantSerializer, OfferSerializer  , OrderSerializer 
from rest_framework.permissions import AllowAny 
from django_filters import rest_framework as filters
from .models import Restaurant, Cuisine, Diet, Offer , Order , VendorFollowed  
from .filters import RestaurantFilter 
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import CoffeeSubscriptionOffer
from .serializers import   CoffeeSubscriptionOfferSerializer , FollowedVendorSerializer 
from django.db.models import Count, Q
from rest_framework import generics, permissions
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet, GenericViewSet
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import MenuCategory, Cart, CartItem, MenuItem, OptionChoice, OptionGroup
from .serializers import (
    MenuCategorySerializer, CartSerializer, CartItemSerializer,
    AddCartItemSerializer, UpdateCartItemSerializer, MenuItemSerializer
)




from rest_framework.filters import SearchFilter

class RestaurantListView(ListAPIView):
    permission_classes = [AllowAny]
    """
    API endpoint to list all available restaurants.
    """
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    filterset_class = RestaurantFilter




class OfferDetailView(RetrieveAPIView):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class FavoriteToggleView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request, pk, format=None):
        try:
            offer = Offer.objects.get(pk=pk)
        except Offer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        user = request.user

        if offer.favorited_by.filter(pk=user.pk).exists():
            offer.favorited_by.remove(user)
            return Response({"detail": "Removed from favorites."}, status=status.HTTP_200_OK)

        else:
            offer.favorited_by.add(user)
            return Response({"detail": "Added to favorites."}, status=status.HTTP_200_OK)


class FavoriteOffersListView(ListAPIView):
    serializer_class = OfferSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return self.request.user.favorite_offers.all()

    

# For QR code views.py 
class PretCoffeeSubscriptionAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        try:
            offer = CoffeeSubscriptionOffer.objects.get(is_active=True)
            if offer.is_expired():
                error_message = {
               
                    "details": "Sorry, this offer has expired."
                }
                return Response(error_message, status=status.HTTP_410_GONE)
            serializer = CoffeeSubscriptionOfferSerializer(offer)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except CoffeeSubscriptionOffer.DoesNotExist:
            error_message = {
          
                "details": "No active offer found."
            }
            return Response(error_message, status=status.HTTP_404_NOT_FOUND)
        
class OrderListView(ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
    
        user = self.request.user
        queryset = Order.objects.filter(user=user).order_by('-created_at') 

        status = self.request.query_params.get('status', None)
        if status is not None and status in ['active', 'completed', 'cancelled']:
            queryset = queryset.filter(status=status)
            
        return queryset
    



class VendorSearchListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = VendorFollowed.objects.all()
    serializer_class = FollowedVendorSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category']
    search_fields = ['name']


# for menu  ***************************************************************************************




# 👇👇👇 নিশ্চিত করুন যে আপনার ViewSet-টি এমন দেখাচ্ছে 👇👇👇
class MenuCategoryViewSet(ModelViewSet):
    """
    এই ViewSet-টি মেনু ক্যাটাগরি এবং এর আইটেমগুলো পরিচালনা করে।
    """
    # --- এই দুটি লাইন থাকা আবশ্যক ---
    queryset = MenuCategory.objects.prefetch_related(
        'items__option_title__options'
    ).all()
    serializer_class = MenuCategorySerializer
    # ---------------------------------

    @action(detail=True, methods=['patch'], url_path='update-item-selection')
    def update_item_selection(self, request, pk=None):
        # ... আপনার কাস্টম অ্যাকশনের বাকি কোড ...
        category = self.get_object()
        
        item_id = request.data.get('item_id')
        option_id = request.data.get('option_id')
        add_to_cart_value = request.data.get('added_to_cart')
        is_selected_value = request.data.get('is_selected')

        try:
            menu_item = MenuItem.objects.get(id=item_id, category=category)
        except MenuItem.DoesNotExist:
            return Response({"error": f"MenuItem with id {item_id} not found in this category."}, status=status.HTTP_404_NOT_FOUND)

        if add_to_cart_value is not None:
            menu_item.added_to_cart = add_to_cart_value
            menu_item.save(update_fields=['added_to_cart'])

        if option_id is not None and is_selected_value is not None:
            try:
                valid_option_groups = OptionGroup.objects.filter(item=menu_item)
                option = OptionChoice.objects.get(id=option_id, group__in=valid_option_groups)
                option.is_selected = is_selected_value
                option.save(update_fields=['is_selected'])
            except OptionChoice.DoesNotExist:
                return Response({"error": f"OptionChoice with id {option_id} not found for this item."}, status=status.HTTP_404_NOT_FOUND)

        refreshed_category = MenuCategory.objects.get(id=pk)
        serializer = self.get_serializer(refreshed_category)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class CartViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    """
    ব্যবহারকারীর কার্ট দেখা এবং ডেলিভারি টাইপ আপডেট করার জন্য একটি এন্ডপয়েন্ট।
    GET /api/cart/
    PATCH /api/cart/
    """
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """ বর্তমান ব্যবহারকারীর জন্য কার্ট অবজেক্ট খুঁজে বের করে বা তৈরি করে। """
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def list(self, request, *args, **kwargs):
        """ GET রিকোয়েস্টের জন্য retrieve মেথড কল করে। """
        return self.retrieve(request, *args, **kwargs)

class CartItemViewSet(ModelViewSet):
    """
    কার্টে আইটেম যোগ, আপডেট, ডিলিট এবং পরিমাণ পরিবর্তন করার জন্য একটি এন্ডপয়েন্ট।
    """
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """ শুধুমাত্র বর্তমান ব্যবহারকারীর কার্টের আইটেমগুলো রিটার্ন করে। """
        return CartItem.objects.filter(
            cart__user=self.request.user
        ).select_related('menu_item').prefetch_related('selected_options')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddCartItemSerializer
        if self.request.method == 'PATCH':
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        """ সিরিয়ালাইজারকে কার্ট অবজেক্ট পাস করে। """
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return {'cart': cart, 'request': self.request}

    @action(detail=True, methods=['post'])
    def increase_quantity(self, request, pk=None):
        """ একটি নির্দিষ্ট কার্ট আইটেমের পরিমাণ ১ বাড়ায়। """
        cart_item = self.get_object()
        cart_item.increase_quantity()
        return Response({'status': 'quantity increased'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def decrease_quantity(self, request, pk=None):
        """ একটি নির্দিষ্ট কার্ট আইটেমের পরিমাণ ১ কমায়। """
        cart_item = self.get_object()
        cart_item.decrease_quantity()
        # যদি আইটেম ডিলিট হয়ে যায়, তাহলে 204 No Content পাঠানো যেতে পারে
        if not CartItem.objects.filter(pk=pk).exists():
            return Response({'status': 'item removed'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'status': 'quantity decreased'}, status=status.HTTP_200_OK)