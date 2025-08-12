# your_app/views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.db.models import Q, Sum
from rest_framework import generics, views, response, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Category, Shop, SearchQuery
from .serializers import (
    CategorySerializer, 
    ShopSerializer, 
    RecentSearchSerializer, 
    FrequentSearchSerializer
)

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

            # যদি ১০টি ইউনিক সার্চ পাওয়া যায়, তবে লুপ বন্ধ করে দিন
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
        ).order_by('-total_searches')[:10] # সেরা ১০টি দেখানো হচ্ছে
        
        serializer = FrequentSearchSerializer(frequent_queries, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

# ৫. মূল Search এবং Filter API
class ShopFilterView(generics.ListAPIView):
    
    permission_classes = [AllowAny]
    """
    এই একটি মাত্র এপিআই সব ধরনের ফিল্টার এবং সর্টিং সমর্থন করে।
    যেমন: পিক-আপ, ডেলিভারি, অফার, দাম, রেটিং এবং সর্টিং।
    """
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    
    # ফিল্টারিং এবং সর্টিংয়ের জন্য Backend যোগ করা হলো
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    
    # কোন কোন ফিল্ডের উপর ভিত্তি করে ফিল্টার করা যাবে তা নির্ধারণ করা
    filterset_fields = {
        'category': ['exact'],
        'allows_pickup': ['exact'],
        'has_offers': ['exact'],
        'price_range': ['exact', 'in'], # 'in' দিয়ে একাধিক রেঞ্জও পাঠানো যাবে
        'is_beyond_neighborhood': ['exact'],
        'rating': ['gte'], # gte = greater than or equal (এর চেয়ে বেশি বা সমান)
    }
    
    # কোন কোন ফিল্ডের উপর ভিত্তি করে সর্ট করা যাবে
    ordering_fields = ['rating', 'delivery_time_minutes', 'delivery_fee']