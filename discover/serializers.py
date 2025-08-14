from rest_framework import serializers
from .models import Restaurant
from .models import Restaurant, Cuisine, Diet





class CuisineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuisine
        fields = ['name']

class DietSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diet
        fields = ['name']



class RestaurantSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
      
    cuisines = CuisineSerializer(many=True, read_only=True)
    diets = DietSerializer(many=True, read_only=True)

    class Meta:
        model = Restaurant
        fields = [
            'id',
            'name',
            'logo',  
            'rating',
            'review_count',
            'distance_km',
            'tags',
            'discount_percentage',
            'logo_url',
            'cuisines', # নতুন ফিল্ড
            'diets',    # নতুন ফিল্ড
            'average_price',
        ]
      
        extra_kwargs = {
            
            'logo': {'write_only': True},
        }

    def get_logo_url(self, obj):
        if obj.logo:
            return obj.logo.url
        return None