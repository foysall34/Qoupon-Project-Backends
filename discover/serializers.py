from rest_framework import serializers
from .models import Restaurant , Offer
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
    


class NestedRestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ['name', 'logo']


class OfferSerializer(serializers.ModelSerializer):
    # সম্পর্কযুক্ত রেস্টুরেন্টের তথ্য দেখানোর জন্য
    restaurant = NestedRestaurantSerializer(read_only=True)
    
    # বর্তমান ইউজার অফারটি ফেভারিট করেছে কিনা তা দেখানোর জন্য
    is_favorited = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = [
            'id',
            'title',
            'description',
            'image',
            'valid_until',
            'discount_percentage',
            'redemption_methods',
            'delivery_cost',
            'min_order_amount',
            'restaurant',
            'is_favorited' # নতুন ফিল্ড
        ]

    def get_is_favorited(self, obj):
        # রিকোয়েস্ট থেকে ইউজারকে নিই
        user = self.context['request'].user
        # যদি ইউজার লগইন করা না থাকে, তাহলে False পাঠাই
        if not user.is_authenticated:
            return False
        # চেক করি ইউজার 'favorited_by' লিস্টে আছে কিনা
        return obj.favorited_by.filter(pk=user.pk).exists()