
from rest_framework import serializers
from .models import Business_profile
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
    