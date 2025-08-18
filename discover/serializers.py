from rest_framework import serializers 
from .models import Restaurant , Offer , Order , VendorFollowed , MenuItem , MenuCategory
from .models import Restaurant, Cuisine, Diet , CoffeeSubscriptionOffer ,CartItem, Cart, CustomizationOption
from decimal import Decimal




class CuisineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuisine
        fields = ['name']

class DietSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diet
        fields = ['name']



class RestaurantSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
      
    cuisines = CuisineSerializer(many=True, read_only=True)
    diets = DietSerializer(many=True, read_only=True)

    class Meta:
        model = Restaurant
        fields = [
            'id',
            'name',
            'logo',  
            'rating',
            'review_count',
            'distance_km',
            'tags',
            'discount_percentage',
            'logo_url',
            'cuisines', 
            'diets',    
            'average_price',
        ]
      
        extra_kwargs = {
            
            'logo': {'write_only': True},
        }

    def get_logo_url(self, obj):
        if obj.logo:
            return obj.logo.url
        return None
    


class NestedRestaurantSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = ['name', 'logo' ,'logo_url']
        extra_kwargs = {
            
            'logo': {'write_only': True},
        }

    def get_logo_url(self, obj):
        if obj.logo:
            return obj.logo.url
        return None

        


class OfferSerializer(serializers.ModelSerializer):
    restaurant = NestedRestaurantSerializer(read_only=True)
    
  
    is_favorited = serializers.SerializerMethodField()
    offer_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = [
            'id',
            'title',
            'description',
            'image',
            'valid_until',
            'discount_percentage',
            'redemption_methods',
            'delivery_cost',
            'min_order_amount',
            'restaurant',
            'is_favorited',
            'offer_image'
        ]
        extra_kwargs = {
            
            'image': {'write_only': True},
         }


    def get_offer_image(self, obj):
        if obj.image:
            return obj.image.url
        return None



    def get_is_favorited(self, obj):
        user = self.context['request'].user
   
        if not user.is_authenticated:
            return False
        return obj.favorited_by.filter(pk=user.pk).exists()
    


class CoffeeSubscriptionOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoffeeSubscriptionOffer
        fields = ['title', 'description', 'price_details', 'offer_details', 'website_url']



class OrderSerializer(serializers.ModelSerializer):
    product_image_url = serializers.SerializerMethodField()
    class Meta:
        model = Order
        fields = [
            'id',
            'order_id',
            'product_name',
            'product_image',
            'price',
            'status',
            'order_type',
            'created_at',
            'product_image_url'
        ]
        extra_kwargs = {
            
            'product_image': {'write_only': True},
         }

    def get_product_image_url(self, obj):
        if obj.product_image:
            return obj.product_image.url
        return None



class FollowedVendorSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = VendorFollowed
        fields = [
            'id',
            'title',
            'category',
            'logo',
            'logo_url',
            'is_followed',
            'descriptions' ,
            'expiry_date',


        ]
        extra_kwargs = {
            
            'logo': {'write_only': True},
         }

    def get_logo_url(self, obj):
        if obj.logo:
            return obj.logo.url
        return None
    

class MenuItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'price', 'calories', 'image' , 'image_url']
        extra_kwargs = {
            
            'image': {'write_only': True},
         }

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

class MenuCategorySerializer(serializers.ModelSerializer):
    """
    ক্যাটাগরি এবং তার অধীনে থাকা সমস্ত আইটেম একসাথে দেখানোর জন্য সিরিয়ালাইজার।
    """
    items = MenuItemSerializer(many=True, read_only=True) # <-- নেস্টেড সিরিয়ালাইজার

    class Meta:
        model = MenuCategory
        fields = ['id', 'name', 'items']

# payment *************************************************************************


class MenuItemSerializer2(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['name', 'image']



class CustomizationOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomizationOption
        fields = ['name', 'additional_price']

class CartItemSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer(read_only=True)
    selected_options = CustomizationOptionSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'menu_item', 'quantity', 'selected_options', 'total_price']
    
    def get_total_price(self, obj):
        # একটি আইটেমের মোট মূল্য = (বেস মূল্য + কাস্টমাইজেশন মূল্য) * পরিমাণ
        base_price = obj.menu_item.price
        options_price = sum(option.additional_price for option in obj.selected_options.all())
        return (base_price + options_price) * obj.quantity

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    sub_total = serializers.SerializerMethodField()
    delivery_charges = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'delivery_type', 'items', 'sub_total', 'delivery_charges', 'total']
    
    def get_sub_total(self, obj):
        # সব আইটেমের মোট মূল্য যোগ করে সাব-টোটাল গণনা
        return sum(
            (item.menu_item.price + sum(opt.additional_price for opt in item.selected_options.all())) * item.quantity
            for item in obj.items.all()
        )
    
    def get_delivery_charges(self, obj):
        if obj.delivery_type == 'delivery' and self.get_sub_total(obj) > 0:
            # 1.99 (float) এর পরিবর্তে Decimal('1.99') ব্যবহার করুন
            return Decimal('1.99')
        # 0.00 (float) এর পরিবর্তে Decimal('0.00') ব্যবহার করুন
        return Decimal('0.00')
        
    def get_total(self, obj):
        return self.get_sub_total(obj) + self.get_delivery_charges(obj)