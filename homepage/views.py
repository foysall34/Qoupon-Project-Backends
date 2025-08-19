# your_app/views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.db.models import Q, Sum
from rest_framework.response import Response
from rest_framework import generics, views, response, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter
from .models import Category, Shop, SearchQuery
from .serializers import (
    CategorySerializer, 
    ShopSerializer, 
    RecentSearchSerializer, 
    FrequentSearchSerializer,
  
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction # অ্যাটমিক অপারেশনের জন্য
from .models import Shop, BusinessHours
from .serializers import BusinessHoursSerializer



# ১. Category List API
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

# ২. Beyond Your Neighborhood API
class BeyondNeighborhoodView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Shop.objects.filter(is_beyond_neighborhood=True)
    serializer_class = ShopSerializer
   

# ৩. Recent Search API
class RecentSearchView(generics.ListAPIView):

    serializer_class = RecentSearchSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        # ধাপ ১: ইউজারের সব সার্চ সবচেয়ে নতুন থেকে পুরনো ক্রমে সাজানো হলো
        all_user_searches = SearchQuery.objects.filter(user=self.request.user).order_by('-created_at')

        unique_recent_searches = []
        seen_queries = set() 

        for search in all_user_searches:
            if search.query_text not in seen_queries:
               
                unique_recent_searches.append(search)
                seen_queries.add(search.query_text)

            if len(unique_recent_searches) >= 10:
                break
        
        return unique_recent_searches

# ৪. Frequently Searched API
class FrequentSearchView(views.APIView):
   
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        # একই query_text গ্রুপ করে search_count যোগ করা হচ্ছে
        frequent_queries = SearchQuery.objects.values('query_text').annotate(
            total_searches=Sum('search_count')
        ).order_by('-total_searches')[:10] 
        
        serializer = FrequentSearchSerializer(frequent_queries, many=True)
       
       
        return response.Response(serializer.data, status=status.HTTP_200_OK)



class ShopFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='istartswith')    
    category_name = CharFilter(field_name='category__name', lookup_expr='istartswith')

    class Meta:
        model = Shop
        fields = {
      
            'category': ['exact'],
            'is_premium':['exact'],
            'has_offers': ['exact'],
            'price_range': ['exact', 'in'],
            'is_beyond_neighborhood': ['exact'],
            'rating': ['gte'],
        }


class ShopFilterView(generics.ListAPIView):
    
    permission_classes = [AllowAny]
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    
    # filterset_fields এর পরিবর্তে filterset_class ব্যবহার করুন
    filterset_class = ShopFilter
    
    ordering_fields = ['rating', 'delivery_time_minutes', 'delivery_fee']


    def list(self, request, *args, **kwargs):
        # প্রথমে ডিফল্ট ফিল্টারিং চালিয়ে কোয়েরিসেটটি নিন
        queryset = self.filter_queryset(self.get_queryset())

       
        if 'category_name' in request.query_params and not queryset.exists():
            return Response(
                {"detail": "Sorry,,This Category not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    


class BusinessHoursView(APIView):
    # এখানে পারমিশন ক্লাস যোগ করতে পারেন, যেমন IsAuthenticated
    # permission_classes = [IsAuthenticated]

    def get(self, request, shop_id):
        """ একটি শপের বর্তমান সময়সূচি রিটার্ন করে। """
        shop = get_object_or_404(Shop, id=shop_id)
        
        # সপ্তাহের সব দিনের জন্য ডেটা তৈরি করুন, এমনকি যদি সেট করা না থাকে
        all_hours = []
        days_of_week = [0, 1, 2, 3, 4, 5, 6] # Mon to Sun
        
        # ডেটাবেস থেকে vorhandene সময়সূচি আনুন
        existing_hours = {bh.day: bh for bh in shop.business_hours.all()}
        
        for day in days_of_week:
            if day in existing_hours:
                serializer = BusinessHoursSerializer(existing_hours[day])
                all_hours.append(serializer.data)
            else:
                # যদি ডেটা সেট করা না থাকে, তাহলে ডিফল্ট মান দিন
                all_hours.append({
                    "day": day,
                    "open_time": None,
                    "close_time": None,
                    "is_closed": True # ডিফল্টভাবে বন্ধ
                })
                
        return Response(all_hours, status=status.HTTP_200_OK)

    def post(self, request, shop_id):
        """ একটি শপের জন্য সপ্তাহের সাত দিনের সময়সূচি সেভ/আপডেট করে। """
        shop = get_object_or_404(Shop, id=shop_id)
        hours_data = request.data
        
        # নিশ্চিত করুন যে ডেটা একটি লিস্ট
        if not isinstance(hours_data, list):
            return Response({"error": "Request data must be a list of business hours."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = BusinessHoursSerializer(data=hours_data, many=True)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # লুপ করে প্রতিটি দিনের জন্য ডেটা সেভ বা আপডেট করুন
                    for item in serializer.validated_data:
                        BusinessHours.objects.update_or_create(
                            shop=shop,
                            day=item['day'],
                            defaults={
                                'open_time': item['open_time'],
                                'close_time': item['close_time'],
                                'is_closed': item['is_closed']
                            }
                        )
                return Response({"message": "Business hours updated successfully."}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)