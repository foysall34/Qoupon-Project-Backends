from rest_framework import serializers 
from .models import Restaurant , Offer , Order , VendorFollowed 
from .models import Restaurant, Cuisine, Diet , CoffeeSubscriptionOffer 
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
    
# cart + menu + payment *********************
# your_app/serializers.py

from rest_framework import serializers
from .models import (
    MenuCategory, MenuItem, OptionGroup, OptionChoice, Cart, CartItem
)


class OptionChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptionChoice
        fields = ['id', 'name', 'price', 'is_selected']

class OptionGroupSerializer(serializers.ModelSerializer):
    options = OptionChoiceSerializer(many=True)
    class Meta:
        model = OptionGroup
        fields = ['id', 'title', 'is_required', 'options']

class MenuItemSerializer(serializers.ModelSerializer):
    option_title = OptionGroupSerializer(many=True)
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = MenuItem
        fields = [
            'id', 'name', 'description', 'price', 'calories', 
            'image','image_url', 'added_to_cart', 'option_title'
        ]

        extra_kwargs = {
            'image': {'write_only': True}
        }
    def get_image_url(self, obj):
        
        if obj.image:
            return obj.image.url
        return None 
        


class MenuCategorySerializer(serializers.ModelSerializer):
    items = MenuItemSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True, allow_null=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    total_price = serializers.SerializerMethodField() 

    class Meta:
        model = MenuCategory
      
        fields = ['id', 'user_id', 'user_email', 'name', 'total_price', 'items']

    def get_total_price(self, obj):
        """
        এই মেথডটি `total_price` ফিল্ডের মান গণনা করে।
        obj হলো MenuCategory-এর একটি instance।
        """
        total = Decimal('0.00')
    
        for item in obj.items.all():
            # যদি আইটেমটি কার্টে যোগ করা থাকে
            if item.added_to_cart:
                total += item.price
                
                # আইটেমের অপশনগুলো লুপ করুন
                for option_group in item.option_title.all():
                    for option in option_group.options.all():
                        # যদি অপশনটি সিলেক্ট করা থাকে
                        if option.is_selected:
                            total += option.price
                            
        return total



class CartItemSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer(read_only=True)
    selected_options = OptionChoiceSerializer(many=True, read_only=True)
    add_to_cart_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = [
            'id', 'menu_item', 'quantity', 'selected_options', 
            'add_to_cart_price', 'total_price'
        ]

class AddCartItemSerializer(serializers.ModelSerializer):
    menu_item_id = serializers.IntegerField(write_only=True)
    option_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=[], write_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'menu_item_id', 'quantity', 'option_ids']
        read_only_fields = ['id']

    def create(self, validated_data):
        cart = self.context['cart']
        menu_item_id = validated_data['menu_item_id']
        quantity = validated_data['quantity']
        option_ids = validated_data['option_ids']
  
        cart_item = CartItem.objects.create(cart=cart, menu_item_id=menu_item_id, quantity=quantity)
        if option_ids:
            options = OptionChoice.objects.filter(id__in=option_ids)
            cart_item.selected_options.set(options) 
        return cart_item

class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']
        extra_kwargs = {
            'quantity': {'min_value': 1}
        }

class CartSerializer(serializers.ModelSerializer):
    """ সম্পূর্ণ কার্ট দেখানোর জন্য। """
    items = CartItemSerializer(many=True, read_only=True)
    price_summary = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source = 'user.email' , read_only = True , allow_null=True )

    class Meta:
        model = Cart
        fields = ['id','user_email', 'user', 'delivery_type', 'items', 'price_summary']
        read_only_fields = ['id', 'user' , 'user_email']

    def get_price_summary(self, cart: Cart) -> dict:
        return {
            'sub_total_price': cart.sub_total_price,
            'delivery_charges': cart.delivery_charges,
            'in_total_price': cart.in_total_price
        }






