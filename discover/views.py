from rest_framework.generics import ListAPIView
from .models import Restaurant
from .serializers import RestaurantSerializer
from rest_framework.permissions import AllowAny 
from django_filters import rest_framework as filters
from .models import Restaurant, Cuisine, Diet
from .filters import RestaurantFilter 


class RestaurantListView(ListAPIView):
    
    permission_classes = [AllowAny]
    """
    API endpoint to list all available restaurants.
    """
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer

    filterset_class = RestaurantFilter




    
    # ফিল্টার ক্লাস যুক্ত করুন
