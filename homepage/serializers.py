# your_app/serializers.py

from rest_framework import serializers
from .models import Category, Shop, SearchQuery

class CategorySerializer(serializers.ModelSerializer):
  
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'image_url', 'image']
        extra_kwargs = {
            'image': {'write_only': True}
        }

    # fucntion of make url 
    def get_image_url(self, obj):
        
        if obj.image:
           
            return obj.image.url
        return None 

class ShopSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Shop
        fields = [
            'id',
            'name',
            'category',
            'category_name',
            'description',
            'logo', # Cloudinary URL
            'cover_image', # Cloudinary URL
            'rating',
            'delivery_fee',
            'delivery_time_minutes',
            'distance_miles',
            'is_beyond_neighborhood',
            'allows_pickup', 'has_offers', 'price_range'
        ]

class RecentSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchQuery
        fields = ['query_text']

class FrequentSearchSerializer(serializers.Serializer):
    query_text = serializers.CharField()
    total_searches = serializers.IntegerField()