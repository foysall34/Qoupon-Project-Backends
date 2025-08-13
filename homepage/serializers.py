

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
    
    # এই দুটি ফিল্ডের ভ্যালু নিচের কাস্টম মেথড থেকে আসবে
    logo_url = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Shop
        fields = [
            'id',
            'name',
            'category',
            'category_name',
            'description',
            'logo_url',          
            'cover_image_url',   
            'rating',
            'delivery_fee',
            'delivery_time_minutes',
            'distance_miles',
            'is_beyond_neighborhood',
            'allows_pickup', 
            'has_offers', 
            'price_range',
            'logo',              # only for use write 
            'cover_image',  
             'is_premium'      # Only for use write
        ]
        extra_kwargs = {
            
            'logo': {'write_only': True},
            'cover_image': {'write_only': True}, 
            'category': {'write_only': True}
        }

    def get_logo_url(self, obj):
   
        # যদি অবজেক্টের সাথে logo যুক্ত থাকে
        if obj.logo:
            # return url from cloudinary 
            return obj.logo.url
        # Otherwiese return None
        return None

    def get_cover_image_url(self, obj):     
        if obj.cover_image:
            return obj.cover_image.url     
        return None




class RecentSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchQuery
        fields = ['query_text']

class FrequentSearchSerializer(serializers.Serializer):
    query_text = serializers.CharField()
    total_searches = serializers.IntegerField()