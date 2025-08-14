from rest_framework.generics import ListAPIView
from .models import Restaurant
from .serializers import RestaurantSerializer, OfferSerializer 
from rest_framework.permissions import AllowAny 
from django_filters import rest_framework as filters
from .models import Restaurant, Cuisine, Diet, Offer
from .filters import RestaurantFilter 
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


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

    
    # ফিল্টার ক্লাস যুক্ত করুন
