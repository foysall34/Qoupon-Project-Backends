from rest_framework import serializers
from .models import Category, Shop, SearchQuery , BusinessHours
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()



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
    shop_logo_url = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    status_text = serializers.SerializerMethodField()
    
    
    class Meta:
        model = Shop
        fields = [
            'id',
            'name',
            'category',
            'category_name',
            'description',
            'shop_title',
            'shop_logo_url',        
            'cover_image_url',   
            'rating',
            'delivery_fee',
            'delivery_time_minutes',
            'distance_miles',
            'is_beyond_neighborhood',
            'has_offers', 
            'price_range',
            'logo',              # only for use write 
            'cover_image',  
            'is_premium',
            'status_text',
            'shop_address', 
            'latitude',
            'longitude' ,
            'offers',
            'deal_validity',
            'redemption_type',
            'is_favourite',
            'min_order'

                                # Only for use write
        ]
        extra_kwargs = {
            
            'logo': {'write_only': True},
            'cover_image': {'write_only': True}, 
            'category': {'write_only': True}
        }


   
    def get_shop_logo_url(self, obj):
        if obj.logo:
            # return url from cloudinary 
            return obj.logo.url
        # Otherwiese return None
        return None

    def get_cover_image_url(self, obj):     
        if obj.cover_image:
            return obj.cover_image.url     
        return None
    
    def get_status_text(self, obj):
        now = timezone.now()
        current_day = now.weekday()
        current_time = now.time()

        try:
            today_hours = obj.business_hours.get(day=current_day)
        except BusinessHours.DoesNotExist:
            return "Closed"

        if today_hours.is_closed:
            return "Closed"
        
        # open_time এবং close_time null নয় তা নিশ্চিত করুন
        if not today_hours.open_time or not today_hours.close_time:
            return "Not available"

        if today_hours.open_time <= current_time < today_hours.close_time:
            if obj.delivery_time_minutes:
                return f"{obj.delivery_time_minutes} min"
            return "Open"
        elif current_time < today_hours.open_time:
            return f"Open {today_hours.open_time.strftime('%I:%M %p').lstrip('0')}"
        else:
            return "Closed" 


class BusinessHoursSerializer(serializers.ModelSerializer):
  
    day = serializers.CharField(source='get_day_display')
    
    class Meta:
        model = BusinessHours
        fields = [ 'day', 'open_time', 'close_time', 'is_closed']

class BusinessHoursCreateUpdateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = BusinessHours
        fields = [ 'user', 'shop', 'day', 'open_time', 'close_time', 'is_closed']
        read_only_fields = ['shop'] # shop ফিল্ডটি URL থেকে আসবে, বডি থেকে নয়

    def validate(self, data):
        is_closed = data.get('is_closed', False)
        if not is_closed and (data.get('open_time') is None or data.get('close_time') is None):
            raise serializers.ValidationError("If the shop is not closed, open and close times are required.")
        if is_closed:
            data['open_time'] = None
            data['close_time'] = None
        return data


class RecentSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchQuery
        fields = ['query_text']

class FrequentSearchSerializer(serializers.Serializer):
    query_text = serializers.CharField()
    total_searches = serializers.IntegerField()