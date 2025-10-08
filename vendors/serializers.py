
from rest_framework import serializers
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from .models import (
    Business_profile, 
    Business_profile_Category, 
    WishDeal,
    Deal, 
    Vendor_Category, 
    Create_Deal, 
    DeliveryCost,
    Image
)

User = get_user_model()


class BusinessProfileCategorySerializer(serializers.ModelSerializer):
    logo_image = serializers.SerializerMethodField()
    class Meta:
        model = Business_profile_Category
        fields =  [ 'id','name' , 'category_image' , 'logo_image']
        extra_kwargs = {
            
            'category_image': {
            'write_only': True,
         
            
            },}
    def get_logo_image(self, obj):
        if obj.category_image:
            return obj.category_image.url
        return None





class Business_profile_Serializer(serializers.ModelSerializer):
    vendor_email = serializers.ReadOnlyField(source='owner.email') 
    vendor_id = serializers.ReadOnlyField(source = 'owner.id' )
    logo_image = serializers.SerializerMethodField()

    class Meta:
        model = Business_profile
        fields = [
            'id',
            'vendor_email',
            'vendor_id',
            'name',
            'logo',
            'logo_image',
            'kvk_number',
            'phone_number',
            'address',
            'category'
        ]

        extra_kwargs = {
            
            'logo': {
            'write_only': True,
            'required': True 
            
            },
       
         }
        
    def get_logo_image(self, obj):
        if obj.logo:
            return obj.logo.url
        return None

from django.contrib.auth import get_user_model
from rest_framework import serializers

class BusinessProfileDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business_profile
        fields = [
            'name',
            'logo',
            'phone_number',
            'kvk_number',
            'address'
        ]


User = get_user_model()

class FollowerSerializer(serializers.ModelSerializer):
    business_profile = BusinessProfileDetailsSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "business_profile"]



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor_Category
        fields = ['id', 'category_title']
        ref_name = "VendorCategory"

class DealSerializer(serializers.ModelSerializer):
    """
    Serializer for the Deal model.
    """
    email = serializers.ReadOnlyField(source='user.email')
    category = CategorySerializer(read_only=True)
    user_id = serializers.ReadOnlyField(source='user.id')
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor_Category.objects.all(),
        source='category',
        write_only=True,
        required=True
    )
    logo_image = serializers.SerializerMethodField()

    def validate_modifiers(self, value):
        """
        Validate the modifiers JSON structure
        """
        if not isinstance(value, list):
            raise serializers.ValidationError("Modifiers must be a list")
        
        for modifier in value:
            if not isinstance(modifier, dict):
                raise serializers.ValidationError("Each modifier must be an object")
            
            required_fields = {'name', 'is_required', 'options'}
            if not all(field in modifier for field in required_fields):
                raise serializers.ValidationError(
                    f"Each modifier must contain {required_fields}"
                )
            
            if not isinstance(modifier['options'], list):
                raise serializers.ValidationError("Options must be a list")
            
            for option in modifier['options']:
                if not isinstance(option, dict):
                    raise serializers.ValidationError("Each option must be an object")
                
                if 'title' not in option:
                    raise serializers.ValidationError("Each option must have a title")
                
                if 'Price' in option and option['Price'] is not None:
                    try:
                        float(option['Price'])
                    except (TypeError, ValueError):
                        raise serializers.ValidationError("Price must be a number or null")
        
        return value

    def create(self, validated_data):
        """
        Create a new Deal instance and set the user from the request
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    class Meta:
        model = Deal
        fields = [
            'id',
            'user_id',
            'email',
            'title',
            'description',
            'price',
            'image',
            'logo_image',
            'category',
            'category_id',
            'modifiers',
            'created_at'
        ]
        read_only_fields = ['id', 'user_id', 'email', 'created_at', 'category']
        extra_kwargs = {
            'image': {'required': True, 'allow_null': False},
            'title': {'required': True},
            'price': {'required': True}
        }

    def get_logo_image(self, obj):
        if obj.image:
            return obj.image.url
        return None
    

# Createdeals/serializers.py

from .models import Create_Deal, DeliveryCost

class DeliveryCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryCost
        fields = ['zip_code', 'delivery_fee', 'min_order_amount']


class Create_DealSerializer(serializers.ModelSerializer):
    delivery_costs = DeliveryCostSerializer(many=True)
    email = serializers.ReadOnlyField(source='user.email') 
    user_id = serializers.ReadOnlyField(source='user.id')
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Create_Deal
        fields = [
            'id', 
            'user_id', 
            'email', 
            'linked_menu_item', 
            'title', 
            'description', 
            'image',
            'image_url',  
            'discount_value_free',
            'discount_value_paid',
            'deal_type',
            'start_date', 
            'end_date',
            'redemption_type', 
            'max_coupons_total', 
            'max_coupons_per_customer',
            'delivery_costs' ,
            'is_active',
            'qrimage',
            'view_count',
            'activation',
            'redemption',
            'push_sent_count'
        ]
        extra_kwargs = {
            'image': {'write_only': True, 'required': False}
        }

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            if request is not None:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def validate(self, data):
        if 'start_date' in data and 'end_date' in data and data['start_date'] >= data['end_date']:
            raise serializers.ValidationError({"end_date": "End date must be after start date."})
        return data


    def create(self, validated_data):
        delivery_costs_data = validated_data.pop('delivery_costs')
        deal = Create_Deal.objects.create(**validated_data)
        for cost_data in delivery_costs_data:
            DeliveryCost.objects.create(deal=deal, **cost_data)
        return deal

    def update(self, instance, validated_data):
        delivery_costs_data = validated_data.pop('delivery_costs', None)
        instance = super().update(instance, validated_data)

        if delivery_costs_data is not None:
            instance.delivery_costs.all().delete() 
            for cost_data in delivery_costs_data:
                DeliveryCost.objects.create(deal=instance, **cost_data) 
                
        return instance

class Categories_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor_Category
        fields = ['id', 
    'category_title',
    'category_description',
    'category_price',
    'category_image',
    'choice_category' ]
        

from .models import Image

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('image',)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['image'] = instance.image.url
        return representation
    

class WishDealSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishDeal
        fields = ['id', 'user', 'deal', 'added_at']
        read_only_fields = ['id', 'added_at']