from rest_framework import serializers
from .models import Category, Shop, SearchQuery ,BusinessHours
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




class RecentSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchQuery
        fields = ['query_text']

class FrequentSearchSerializer(serializers.Serializer):
    query_text = serializers.CharField()
    total_searches = serializers.IntegerField()


class BusinessHoursSerializer(serializers.ModelSerializer):
    """
    BusinessHours মডেলের ডেটা Serialize এবং Deserialize করার জন্য Serializer।
    """
    # 'day' ফিল্ডটিকে Integer হিসেবে না দেখিয়ে নাম (e.g., "Monday") হিসেবে দেখানোর জন্য।
    # এটি GET request-এ human-readable output দেবে।
    day_display = serializers.CharField(source='get_day_display', read_only=True)

    class Meta:
        model = BusinessHours
        fields = [
            
            'day', 
            'day_display', # এটি শুধুমাত্র GET response-এ দেখা যাবে।
            'open_time', 
            'close_time', 
            'is_closed'
        ]
        
        # 'user' 필্ডটি শুধুমাত্র read-only হিসেবে রাখা হয়েছে, 
        # কারণ এটি request-এর ব্যবহারকারী থেকে স্বয়ংক্রিয়ভাবে সেট হবে, 
        # ক্লায়েন্ট এটি পাঠাতে পারবে না।
        read_only_fields = ['user']

    def validate(self, data):
        """
        ডেটা ভ্যালিডেশনের জন্য কাস্টম লজিক।
        """
        is_closed = data.get('is_closed', False)
        open_time = data.get('open_time')
        close_time = data.get('close_time')

        # যদি is_closed=False হয় (অর্থাৎ খোলা থাকে), তাহলে open_time এবং close_time অবশ্যই থাকতে হবে।
        if not is_closed:
            if open_time is None or close_time is None:
                raise serializers.ValidationError("Business is open, so open_time and close_time are required.")
            
            # open_time অবশ্যই close_time-এর আগে হতে হবে।
            if open_time >= close_time:
                raise serializers.ValidationError("Open time must be earlier than close time.")
        
        # যদি is_closed=True হয়, তাহলে open_time এবং close_time-কে None করে দেওয়া যেতে পারে।
        # এটি ঐচ্ছিক, তবে ডেটা পরিষ্কার রাখতে সাহায্য করে।
        if is_closed:
            data['open_time'] = None
            data['close_time'] = None

        return data

    def create(self, validated_data):
        """
        নতুন BusinessHours অবজেক্ট তৈরি করার সময় user সেট করা।
        """
        # ভিউ থেকে user অবজেক্টটি নিয়ে আসা হচ্ছে।
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        BusinessHours অবজেক্ট আপডেট করার সময় user সেট করা।
        """
        validated_data['user'] = self.context['request'].user
        return super().update(instance, validated_data)