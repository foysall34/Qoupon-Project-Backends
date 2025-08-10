from rest_framework import serializers
from .models import FoodCategory, Fvt_category
from django.contrib.auth import get_user_model
from .models import Place
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable


User = get_user_model()

class FoodCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCategory
        fields = ['id', 'name', 'emoji']



class UserFvtDetailSerializer(serializers.ModelSerializer):
    """
    ইউজারের প্রোফাইল এবং তার পছন্দের ক্যাটাগরি দেখানোর জন্য।
    """
    user_info = serializers.SerializerMethodField()
    
    # এখন FoodCategorySerializer সংজ্ঞায়িত আছে
    favorite_categories = FoodCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Fvt_category
        fields = ['id', 'user_info', 'favorite_categories']
    
    def get_user_info(self, obj):
        """
        ইউজারের তথ্য একটি কাস্টম অবজেক্ট হিসেবে রিটার্ন করে।
        """
        # --- সমাধান ২: obj.user.full_name এর পরিবর্তে obj.user.get_full_name() ব্যবহার ---
        return {
            # অথবা obj.user.username যদি শুধু ইউজারনেম চান
            "email": obj.user.email
        }

# --- Post ---

    

# Google Map serializers
class PlaceSerializer(serializers.ModelSerializer):
    google_maps_url = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = [
            'id', 
            'name', 
            'address', 
            'latitude', 
            'longitude', 
            'google_maps_url',
            'created_at'
        ]
        # latitude এবং longitude শুধুমাত্র দেখানোর জন্য, ইউজার ইনপুট দেবে না
        read_only_fields = ['id', 'latitude', 'longitude', 'google_maps_url', 'created_at']

    def get_google_maps_url(self, obj):
        if obj.latitude and obj.longitude:
            return f"https://www.google.com/maps?q={obj.latitude},{obj.longitude}"
        return "Address could not be geocoded."

    def _get_coordinates(self, address):
        """ Find latitude & longitude function  """
        try:
            geolocator = Nominatim(user_agent="my_place_app") # একটি ইউনিক user_agent দিন
            location = geolocator.geocode(address)
            if location:
                return location.latitude, location.longitude
            return None, None
        except GeocoderUnavailable:
            # যদি জিওকোডিং সার্ভিস কাজ না করে
            raise serializers.ValidationError("Geocoding service is unavailable. Please try again later.")


    def create(self, validated_data):
        """ একটি নতুন স্থান তৈরি করার সময় ঠিকানা থেকে lat/lon বের করা হবে """
        address = validated_data.get('address')
        lat, lon = self._get_coordinates(address)

        if lat is None or lon is None:
            
            raise serializers.ValidationError({"address": "this location can't find ."})

        # নতুন পাওয়া lat/lon ডেটাতে যোগ করা হচ্ছে
        validated_data['latitude'] = lat
        validated_data['longitude'] = lon
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """ স্থান আপডেট করার সময় যদি ঠিকানা পরিবর্তন হয়, তাহলে lat/lon আবার বের করা হবে """
        address = validated_data.get('address', instance.address)

        # if change the location 
        if 'address' in validated_data and validated_data['address'] != instance.address:
            lat, lon = self._get_coordinates(address)
            if lat is None or lon is None:
                raise serializers.ValidationError({"address": "this location can't found .."})
            
            validated_data['latitude'] = lat
            validated_data['longitude'] = lon
            
        return super().update(instance, validated_data)