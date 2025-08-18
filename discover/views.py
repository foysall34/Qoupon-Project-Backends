from rest_framework.generics import ListAPIView
from django.http import Http404
from .models import Restaurant
from .serializers import RestaurantSerializer, OfferSerializer  , OrderSerializer
from rest_framework.permissions import AllowAny 
from django_filters import rest_framework as filters
from .models import Restaurant, Cuisine, Diet, Offer , Order , VendorFollowed , MenuItem, MenuCategory, CartItem, Cart
from .filters import RestaurantFilter 
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import CoffeeSubscriptionOffer
from .serializers import  CartSerializer,CartItemSerializer, CoffeeSubscriptionOfferSerializer , FollowedVendorSerializer , MenuCategorySerializer , MenuItemSerializer
from django.db.models import Count, Q
from rest_framework import generics, permissions
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend


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
    permission_classes = [IsAuthenticated] 

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
    permission_classes = [IsAuthenticated]

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

    queryset = VendorFollowed.objects.all()
    serializer_class = FollowedVendorSerializer
    
 
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category']
    search_fields = ['name']



class MenuView(generics.ListAPIView):

    serializer_class = MenuCategorySerializer

    def get_queryset(self):

        return MenuCategory.objects.prefetch_related('items').all()
    

# for payment ***************************************************************************************
class CartDetailAPIView(APIView):
    """
    লগইন করা ব্যবহারকারীর কার্টের বিস্তারিত তথ্য দেখায় এবং আপডেট করে (e.g., delivery type)।
    GET, PUT, PATCH মেথড হ্যান্ডেল করে।
    """
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        সহায়ক মেথড: বর্তমান ব্যবহারকারীর জন্য কার্ট খুঁজে বের করে বা তৈরি করে।
        """
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def get(self, request, *args, **kwargs):
        """
        কার্টের বিস্তারিত তথ্য দেখানোর জন্য GET রিকোয়েস্ট।
        """
        cart = self.get_object()
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        """
        কার্টের আংশিক তথ্য (যেমন delivery_type) আপডেট করার জন্য PATCH রিকোয়েস্ট।
        """
        cart = self.get_object()
        # 'partial=True' দিয়ে আমরা আংশিক আপডেট করতে পারি
        serializer = CartSerializer(cart, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# CartItemViewSet এর List এবং Create অংশের জন্য
class CartItemListCreateAPIView(APIView):
    """
    ব্যবহারকারীর কার্টে থাকা আইটেমের তালিকা দেখায় (GET) এবং 
    নতুন আইটেম যোগ করে (POST)।
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        কার্টে থাকা সব আইটেমের তালিকা দেখানোর জন্য।
        """
        cart_items = CartItem.objects.filter(cart__user=request.user)
        serializer = CartItemSerializer(cart_items, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """
        কার্টে একটি নতুন আইটেম যোগ করার জন্য।
        """
        serializer = CartItemSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # ব্যবহারকারীর কার্ট খুঁজে বের করে তার সাথে আইটেমটি যুক্ত করে
            cart, created = Cart.objects.get_or_create(user=request.user)
            serializer.save(cart=cart)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# CartItemViewSet এর Retrieve, Update, Delete অংশের জন্য
class CartItemDetailAPIView(APIView):
    """
    একটি নির্দিষ্ট কার্ট আইটেম দেখা (GET), আপডেট করা (PUT/PATCH), 
    এবং ডিলিট করার (DELETE) জন্য।
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        """
        সহায়ক মেথড: একটি নির্দিষ্ট কার্ট আইটেম খুঁজে বের করে, 
        এবং নিশ্চিত করে যে এটি বর্তমান ব্যবহারকারীর।
        """
        try:
            return CartItem.objects.get(pk=pk, cart__user=self.request.user)
        except CartItem.DoesNotExist:
            raise Http404

    def get(self, request, pk, *args, **kwargs):
        """
        একটি নির্দিষ্ট আইটেমের বিস্তারিত তথ্য দেখানোর জন্য।
        """
        cart_item = self.get_object(pk)
        serializer = CartItemSerializer(cart_item, context={'request': request})
        return Response(serializer.data)

    def patch(self, request, pk, *args, **kwargs):
        """
        একটি নির্দিষ্ট আইটেমের পরিমাণ (quantity) আপডেট করার জন্য।
        """
        cart_item = self.get_object(pk)
        serializer = CartItemSerializer(cart_item, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        """
        একটি নির্দিষ্ট আইটেম কার্ট থেকে ডিলিট করার জন্য।
        """
        cart_item = self.get_object(pk)
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)