from rest_framework import serializers
from .models import FoodCategory, UserProfile
from django.contrib.auth import get_user_model
from .models import Place
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable

User = get_user_model()

class FoodCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCategory
        fields = ['id', 'name', 'emoji']

class UserProfileDetailSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()
    favorite_categories = FoodCategorySerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'user_info', 'favorite_categories']
    
    def get_user_info(self, obj):
        return {
            "username": obj.user.full_name,
            "email": obj.user.email
        }


# --- Post ---
class UserProfileCreateSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(write_only=True, help_text="give email ")
    favorite_category_names = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        help_text="show your chooseable : [\"Pizza & Pasta\", \"Asian Cuisine\"]"
    )

    class Meta:
        model = UserProfile
        fields = ['user_email', 'favorite_category_names']

    def create(self, validated_data):
        user_email = validated_data.get('user_email')
        category_names = validated_data.get('favorite_category_names')

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"user_email": f"'{user_email}' doesn't exist ..."})

        # Is exist or not user profile 
        if UserProfile.objects.filter(user=user).exists():
            raise serializers.ValidationError({"user_email": "Prfile already created."})

        # search by category 
        categories = []
        missing_categories = []
        for name in category_names:
            try:
                category = FoodCategory.objects.get(name__iexact=name.strip())
                categories.append(category)
            except FoodCategory.DoesNotExist:
                missing_categories.append(name)
        
        if missing_categories:
            raise serializers.ValidationError({
                "favorite_category_names": f"Doesn't found : {', '.join(missing_categories)}"
            })

        # create new profile & category ..............
        profile = UserProfile.objects.create(user=user)
        profile.favorite_categories.set(categories)
        return profile
    

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