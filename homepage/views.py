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
    filterset_class = ShopFilter
    
    ordering_fields = ['rating', 'delivery_time_minutes', 'delivery_fee']


    def list(self, request, *args, **kwargs):
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
    


# your_app_name/views.py

# home/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import BusinessHours
from .serializers import BusinessHoursSerializer 
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model 

User = get_user_model()

class UserBusinessHoursAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id, *args, **kwargs):
    
        user = get_object_or_404(User, id=user_id)

        queryset = BusinessHours.objects.filter(user=user)
        existing_hours_map = {bh.day: bh for bh in queryset}
        
        full_schedule_list = []

        for day_index, day_name in BusinessHours.DayOfWeek.choices:
            if day_index in existing_hours_map:
                serializer = BusinessHoursSerializer(existing_hours_map[day_index])
                full_schedule_list.append(serializer.data)
            else:
                full_schedule_list.append({
              
                    "day": day_name,
                    "open_time": "00:00:00",
                    "close_time": "23:59:00",
                    "is_closed": False
                })

        response_data = {
            'user_id': user.id,
            'user_email': user.email,
            'schedule': full_schedule_list
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = request.data
        if not isinstance(data, list):
            return Response({"detail": "Request body must be a list of schedule items."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        response_data, error_data = [], []

        for item in data:
            day = item.get('day')
            if day is None:
                error_data.append({'item': item, 'errors': 'Day is required.'})
                continue
            
      
            instance, created = BusinessHours.objects.get_or_create(user=user, day=day)
            
       
            serializer = BusinessHoursSerializer(instance, data=item, context={'request': request})
            
            if serializer.is_valid():
            
                serializer.save(user=user)
                response_data.append(serializer.data)
            else:
                error_data.append({'day': day, 'errors': serializer.errors})

        if error_data:
            return Response(error_data, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(response_data, status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)



