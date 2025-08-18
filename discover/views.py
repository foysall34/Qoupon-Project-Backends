from rest_framework.generics import ListAPIView
from .models import Restaurant
from .serializers import RestaurantSerializer, OfferSerializer  , OrderSerializer
from rest_framework.permissions import AllowAny 
from django_filters import rest_framework as filters
from .models import Restaurant, Cuisine, Diet, Offer , Order , VendorFollowed , MenuItem, MenuCategory
from .filters import RestaurantFilter 
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import CoffeeSubscriptionOffer
from .serializers import CoffeeSubscriptionOfferSerializer , FollowedVendorSerializer , MenuCategorySerializer , MenuItemSerializer
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
    
    # সিরিয়ালাইজারে request অবজেক্ট পাস করার জন্য
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

# ফেভারিট যোগ/বাদ দেওয়ার জন্য ভিউ
class FavoriteToggleView(APIView):
    permission_classes = [IsAuthenticated] # শুধুমাত্র লগইন করা ইউজাররা ব্যবহার করতে পারবে

    def post(self, request, pk, format=None):
        try:
            offer = Offer.objects.get(pk=pk)
        except Offer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        user = request.user
        
        # যদি ইউজার ইতোমধ্যে ফেভারিট করে থাকে, তাহলে রিমুভ করুন
        if offer.favorited_by.filter(pk=user.pk).exists():
            offer.favorited_by.remove(user)
            return Response({"detail": "Removed from favorites."}, status=status.HTTP_200_OK)
        # না হলে, যোগ করুন
        else:
            offer.favorited_by.add(user)
            return Response({"detail": "Added to favorites."}, status=status.HTTP_200_OK)

# ইউজারের সব ফেভারিট অফার দেখানোর জন্য
class FavoriteOffersListView(ListAPIView):
    serializer_class = OfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # শুধুমাত্র বর্তমান ইউজারের ফেভারিট করা অফারগুলো রিটার্ন করুন
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
        """
        এই ভিউটি শুধুমাত্র অথেনটিকেটেড ব্যবহারকারীর অর্ডারগুলো দেখাবে
        এবং 'status' কোয়েরি প্যারামিটার অনুযায়ী ফিল্টার করবে।
        """
        user = self.request.user
        queryset = Order.objects.filter(user=user).order_by('-created_at') # নতুন অর্ডার আগে দেখাবে

        status = self.request.query_params.get('status', None)
        if status is not None and status in ['active', 'completed', 'cancelled']:
            queryset = queryset.filter(status=status)
            
        return queryset
    



class VendorSearchListView(generics.ListAPIView):
    """
    এই ভিউটি ভেন্ডরদের তালিকা দেখাবে এবং 
    'search' ও 'category' প্যারামিটার দিয়ে খোঁজার সুবিধা দেবে।
    """
    queryset = VendorFollowed.objects.all()
    serializer_class = FollowedVendorSerializer
    
    # কোন কোন ব্যাকএন্ড ব্যবহার করা হবে তা নির্ধারণ করা
    filter_backends = [DjangoFilterBackend, SearchFilter]
    
    # DjangoFilterBackend-এর জন্য: কোন কোন ফিল্ড দিয়ে ফিল্টার করা যাবে
    filterset_fields = ['category']
    
    # SearchFilter-এর জন্য: কোন কোন ফিল্ডে সার্চ করা হবে
    search_fields = ['name']



class MenuView(generics.ListAPIView):
    """
    এই ভিউটি সমস্ত মেনু ক্যাটাগরি এবং তাদের অধীনে থাকা আইটেমগুলোর তালিকা দেখাবে।
    """
    serializer_class = MenuCategorySerializer

    def get_queryset(self):
        """
        ডেটাবেস পারফরম্যান্স অপটিমাইজ করার জন্য prefetch_related ব্যবহার করা হয়েছে।
        """
        return MenuCategory.objects.prefetch_related('items').all()