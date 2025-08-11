from rest_framework import serializers
from .models import FoodCategory, Fvt_category
from django.contrib.auth import get_user_model
from .models import Place 
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable
from rest_framework import serializers
from .models import Profile

User = get_user_model()

class FoodCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCategory
        fields = ['id', 'name', 'emoji']

class UserFvtDetailSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()
    favorite_categories = FoodCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Fvt_category
        fields = ['id', 'user_info', 'favorite_categories']
    
    def get_user_info(self, obj):
        return {
            "email": obj.user.email
        }

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
    


# For Profiel page 
class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    # We create a new read-only field that will contain the generated URL.
    profile_picture_url = serializers.SerializerMethodField()  # This serializersMethod use extra field , you can't take input from frontend only show json response

    class Meta:
        model = Profile
        fields = [
            'username',
            'email',
            'full_name',
            'phone_number',
            'language',
            'profile_picture',       # Used for uploads (write-only)
            'profile_picture_url'    # Used for display (read-only)
        ]
        # This ensures the raw 'profile_picture' path isn't in the output.
        extra_kwargs = {
            'profile_picture': {'write_only': True}
        }

    def get_profile_picture_url(self, obj):
        """
        This method is called by the SerializerMethodField to get the value.
        'obj' is the Profile instance.
        """
        if obj.profile_picture:
            # The .url attribute of a CloudinaryField automatically
            # generates the full URL.
            return obj.profile_picture.url
        return None # Or return a default image URL
        