from rest_framework import serializers
from .models import Restaurant , Offer , Order
from .models import Restaurant, Cuisine, Diet , CoffeeSubscriptionOffer





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
            'cuisines', 
            'diets',    
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
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = ['name', 'logo' ,'logo_url']
        extra_kwargs = {
            
            'logo': {'write_only': True},
        }

    def get_logo_url(self, obj):
        if obj.logo:
            return obj.logo.url
        return None

        


class OfferSerializer(serializers.ModelSerializer):
    restaurant = NestedRestaurantSerializer(read_only=True)
    
  
    is_favorited = serializers.SerializerMethodField()
    offer_image = serializers.SerializerMethodField()
    
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
            'is_favorited',
            'offer_image'
        ]
        extra_kwargs = {
            
            'image': {'write_only': True},
         }


    def get_offer_image(self, obj):
        if obj.image:
            return obj.image.url
        return None



    def get_is_favorited(self, obj):
        user = self.context['request'].user
   
        if not user.is_authenticated:
            return False
        return obj.favorited_by.filter(pk=user.pk).exists()
    


class CoffeeSubscriptionOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoffeeSubscriptionOffer
        fields = ['title', 'description', 'price_details', 'offer_details', 'website_url']



class OrderSerializer(serializers.ModelSerializer):
    product_image_url = serializers.SerializerMethodField()
    class Meta:
        model = Order
        fields = [
            'id',
            'order_id',
            'product_name',
            'product_image',
            'price',
            'status',
            'order_type',
            'created_at',
            'product_image_url'
        ]
        extra_kwargs = {
            
            'product_image': {'write_only': True},
         }

    def get_product_image_url(self, obj):
        if obj.product_image:
            return obj.product_image.url
        return None
