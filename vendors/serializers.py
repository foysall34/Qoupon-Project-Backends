
from rest_framework import serializers
from .models import Business_profile, Business_profile_Category
from .models import Deal, Vendor_Category, ModifierGroup
from django_filters.rest_framework import DjangoFilterBackend 
from django.contrib.auth import get_user_model

User = get_user_model()


class BusinessProfileCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Business_profile_Category
        fields = '__all__'





class Business_profile_Serializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username') 
    logo_image = serializers.SerializerMethodField()

    class Meta:
        model = Business_profile
        fields = [
            'id',
            'owner',
            'name',
            'logo',
            'logo_image',
            'kvk_number',
            'phone_number',
            'address',
            'category'
        ]

        extra_kwargs = {
            
            'logo': {'write_only': True},
         }
        
    def get_logo_image(self, obj):
        if obj.logo:
            return obj.logo.url
        return None






class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor_Category
        fields = ['id', 'category_title']

class ModifierGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModifierGroup
        fields = ['id', 'name']

class DealSerializer(serializers.ModelSerializer):
    """
    Serializer for the Deal model.
    """
    # GET রেসপন্সের জন্য user অবজেক্টের বিস্তারিত তথ্য
    email = serializers.ReadOnlyField(source='user.email')
    category = CategorySerializer(read_only=True)
    modifier_groups = ModifierGroupSerializer(many=True, read_only=True)

    # POST/PUT রিকোয়েস্টের জন্য user id ইনপুট নেবে।
    # 'user' মডেলের user ফিল্ডের সাথে এটি ম্যাপ করা।
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=True
    )
    
    # রেসপন্সে user_id দেখানোর জন্য
    user_id = serializers.ReadOnlyField(source='user.id')

    # POST/PUT রিকোয়েস্টের জন্য category_id গ্রহণ করবে
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor_Category.objects.all(),
        source='category',
        write_only=True,
        required=True
    )

    # POST/PUT রিকোয়েস্টের জন্য modifier_group_ids গ্রহণ করবে
    modifier_group_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ModifierGroup.objects.all(),
        source='modifier_groups',
        write_only=True,
        required=False
    )
    
    logo_image = serializers.SerializerMethodField()

    class Meta:
        model = Deal
        fields = [
            'id',
            'user',                 # POST রিকোয়েস্টের জন্য আইডি নেবে
            'user_id',              # GET রেসপন্সের জন্য আইডি দেখাবে
            'email',
            'title',
            'description',
            'price',
            'image',
            'logo_image',
            'category',             # GET-এর জন্য
            'modifier_groups',      # GET-এর জন্য
            'category_id',          # POST/PUT-এর জন্য
            'modifier_group_ids',   # POST/PUT-এর জন্য
            'created_at'
        ]
        
        # 'user' ফিল্ডটি শুধু লেখার জন্য, তাই এটিকে read_only_fields থেকে বাদ দিতে হবে
        read_only_fields = ['id', 'user_id', 'email', 'created_at', 'category', 'modifier_groups']
        
        extra_kwargs = {
            'image': {'required': True, 'allow_null': False},
            'title': {'required': True},
            'price': {'required': True},
            # 'user' ফিল্ডটি শুধুমাত্র আইডি গ্রহণ করবে, পুরো অবজেক্ট নয়
            'user': {'write_only': True}
        }

    def get_logo_image(self, obj):
        # আপনার লজিক অনুযায়ী এখানে লোগো ইমেজের URL রিটার্ন করুন
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
            'discount_value',
            'start_date', 
            'end_date',
            'redemption_type', 
            'max_coupons_total', 
            'max_coupons_per_customer',
            'delivery_costs' 
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