
from rest_framework import serializers
from .models import Business_profile
from .models import Deal, Vendor_Category, ModifierGroup








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
    # Use nested serializers for read-only representations to show full object details.
    category = CategorySerializer(read_only=True)
    modifier_group_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ModifierGroup.objects.all(),
        source='modifier_groups',
        write_only=True,
        required=True,       
        allow_empty=False    
    )


    # Use PrimaryKeyRelatedField for write operations to accept IDs from the client.
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor_Category.objects.all(), source='category', write_only=True
    )
    modifier_group_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=ModifierGroup.objects.all(), source='modifier_groups', write_only=True, required=False
    )
    logo_image = serializers.SerializerMethodField()

    class Meta:
        model = Deal
        fields = [
            'id',
            'title',
            'description',
            'price',
            'image',
            'logo_image',
            'category',             # For GET requests
            'modifier_groups',      # For GET requests
            'category_id',          # For POST/PUT requests
            'modifier_group_ids',   # For POST/PUT requests
            'created_at'
        ]
        extra_kwargs = {
            'image': {
                'required': True,      
                'allow_null': False    
            }
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
  

    class Meta:
        model = Create_Deal
        fields = [
            'id',
            'linked_menu_item',
            'title',
            'description',
            'image',
            'discount_type',
            'discount_value',
            'start_date',
            'end_date',
            'redemption_type',
            'max_coupons_total',
            'max_coupons_per_customer',
            'delivery_costs' 
        ]

    def create(self, validated_data):
        # প্রথমে delivery_costs ডেটা আলাদা করে ফেলা হচ্ছে
        delivery_costs_data = validated_data.pop('delivery_costs')
        
        # মূল Deal অবজেক্ট তৈরি করা হচ্ছে
        deal = Create_Deal.objects.create(**validated_data)
        
        # এখন প্রতিটি delivery_cost ডেটা দিয়ে DeliveryCost অবজেক্ট তৈরি করা হচ্ছে
        for cost_data in delivery_costs_data:
            DeliveryCost.objects.create(deal=deal, **cost_data)
            
        return deal

    def validate(self, data):
        # Start date অবশ্যই end date-এর আগে হতে হবে
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("End date must be after start date.")
        return data
    

# for category (breakfast , lunch , dinner )
class Categories_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor_Category
        fields = ['id', 
    'category_title',
    'category_description',
    'category_price',
    'category_image',
    'choice_category' ]