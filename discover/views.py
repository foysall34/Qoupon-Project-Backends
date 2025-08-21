from rest_framework.generics import ListAPIView
from django.http import Http404
from .models import Restaurant
from .serializers import RestaurantSerializer, OfferSerializer  , OrderSerializer , CartSerializer
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
from .serializers import   CoffeeSubscriptionOfferSerializer , FollowedVendorSerializer , MenuCategorySerializer 
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
class MenuCategoryListAPIView(generics.ListAPIView):
    """
    API endpoint that returns a list of menu categories with nested items and options.
    """
    queryset = MenuCategory.objects.all().prefetch_related(
        'items__option_title__options'
    )
    serializer_class = MenuCategorySerializer



class MenuCategoryDetailAPIView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for retrieving and updating a single menu category.
    """
    queryset = MenuCategory.objects.all().prefetch_related(
        'items__option_title__options'
    )
    serializer_class = MenuCategorySerializer



# for cart viwes.py 
class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CartSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        cart = serializer.save()
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)