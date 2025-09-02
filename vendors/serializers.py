
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
        fields = ['id', 'name']

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
        required=True,       # ফিল্ডটিকে আবশ্যিক করা হলো
        allow_empty=False    # খালি লিস্ট ([]) গ্রহণ করা হবে না
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