from rest_framework.generics import ListAPIView
from django.http import Http404
from .models import FAQ, Restaurant
from .serializers import FAQSerializer, RestaurantSerializer, OfferSerializer  , OrderSerializer 
from rest_framework.permissions import AllowAny 
from django_filters import rest_framework as filters
from .models import Restaurant, Cuisine, Diet, Offer , Order , VendorFollowed  
from .filters import RestaurantFilter 
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import CoffeeSubscriptionOffer
from .serializers import   CoffeeSubscriptionOfferSerializer , FollowedVendorSerializer 
from django.db.models import Count, Q
from rest_framework import generics, permissions
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet, GenericViewSet
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import MenuCategory, Cart, CartItem, MenuItem, OptionChoice, OptionGroup, ReviewMenuItem
from .serializers import (
    MenuCategorySerializer, CartSerializer, CartItemSerializer,
    AddCartItemSerializer, UpdateCartItemSerializer, MenuItemSerializer, ReviewMenuItemSerializer
)




from rest_framework.filters import SearchFilter

class RestaurantListView(ListAPIView):
    permission_classes = [AllowAny]
    """
    API endpoint to list all available restaurants.
    """
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    filterset_class = RestaurantFilter




class OfferDetailView(RetrieveAPIView):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class FavoriteToggleView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request, pk, format=None):
        try:
            offer = Offer.objects.get(pk=pk)
        except Offer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        user = request.user

        if offer.favorited_by.filter(pk=user.pk).exists():
            offer.favorited_by.remove(user)
            return Response({"detail": "Removed from favorites."}, status=status.HTTP_200_OK)

        else:
            offer.favorited_by.add(user)
            return Response({"detail": "Added to favorites."}, status=status.HTTP_200_OK)


class FavoriteOffersListView(ListAPIView):
    serializer_class = OfferSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return self.request.user.favorite_offers.all()

    

# For QR code views.py 
class PretCoffeeSubscriptionAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        try:
            offer = CoffeeSubscriptionOffer.objects.get(is_active=True)
            if offer.is_expired():
                error_message = {
               
                    "details": "Sorry, this offer has expired."
                }
                return Response(error_message, status=status.HTTP_410_GONE)
            serializer = CoffeeSubscriptionOfferSerializer(offer)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except CoffeeSubscriptionOffer.DoesNotExist:
            error_message = {
          
                "details": "No active offer found."
            }
            return Response(error_message, status=status.HTTP_404_NOT_FOUND)
        
class OrderListView(ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
    
        user = self.request.user
        queryset = Order.objects.filter(user=user).order_by('-created_at') 

        status = self.request.query_params.get('status', None)
        if status is not None and status in ['active', 'completed', 'cancelled']:
            queryset = queryset.filter(status=status)
            
        return queryset
    



class VendorSearchListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = VendorFollowed.objects.all()
    serializer_class = FollowedVendorSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category']
    search_fields = ['name']


# -----------------------------for menu  ----------------------------------------


class MenuCategoryListAPIView(APIView):
    """
    একটি নির্দিষ্ট ব্যবহারকারীর জন্য সমস্ত MenuCategory তালিকাভুক্ত করে।
    """
    def get(self, request, user_id, format=None):
        # URL থেকে user_id নিয়ে সেই ব্যবহারকারীর জন্য MenuCategory ফিল্টার করে
        categories = MenuCategory.objects.filter(user_id=user_id).prefetch_related('items__option_title__options')
        serializer = MenuCategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# --- দ্বিতীয় ভিউ: একটি নির্দিষ্ট ক্যাটাগরি এবং তার আইটেম আপডেট করার জন্য ---
class MenuCategoryDetailAPIView(APIView):
    """
    একটি নির্দিষ্ট MenuCategory অবজেক্টের বিস্তারিত তথ্য প্রদান এবং আইটেম আপডেট করে।
    """
    def get_object(self, user_id, pk):
        """
        ডাটাবেস থেকে একটি নির্দিষ্ট MenuCategory অবজেক্ট খুঁজে বের করে।
        """
        try:
            # user_id এবং pk উভয় দিয়েই ফিল্টার করা হচ্ছে নিরাপত্তার জন্য
            return MenuCategory.objects.get(user_id=user_id, pk=pk)
        except MenuCategory.DoesNotExist:
            raise Http404

    def get(self, request, user_id, pk, format=None):
        """
        একটি নির্দিষ্ট MenuCategory-এর বিস্তারিত তথ্য দেখায়।
        """
        category = self.get_object(user_id, pk)
        serializer = MenuCategorySerializer(category)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, user_id, pk, format=None):
        """
        'update-item-selection' এর কার্যকারিতা এখানে প্রয়োগ করা হয়েছে।
        এটি একটি MenuItem-এর 'added_to_cart' অথবা একটি OptionChoice-এর 'is_selected' স্ট্যাটাস আপডেট করে।
        """
        category = self.get_object(user_id, pk)
        
        item_id = request.data.get('item_id')
        option_id = request.data.get('option_id')
        add_to_cart_value = request.data.get('added_to_cart')
        is_selected_value = request.data.get('is_selected')

        # item_id এবং অন্যান্য প্রয়োজনীয় ডেটা অনুরোধে আছে কিনা তা পরীক্ষা করুন
        if not item_id:
            return Response({"error": "item_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            menu_item = MenuItem.objects.get(id=item_id, category=category)
        except MenuItem.DoesNotExist:
            return Response({"error": f"MenuItem with id {item_id} not found in this category."}, status=status.HTTP_404_NOT_FOUND)

        if add_to_cart_value is not None:
            menu_item.added_to_cart = add_to_cart_value
            menu_item.save(update_fields=['added_to_cart'])

        if option_id is not None and is_selected_value is not None:
            try:
                # নিশ্চিত করুন যে অপশনটি এই আইটেমের অন্তর্গত
                valid_option_groups = OptionGroup.objects.filter(item=menu_item)
                option = OptionChoice.objects.get(id=option_id, group__in=valid_option_groups)
                option.is_selected = is_selected_value
                option.save(update_fields=['is_selected'])
            except OptionChoice.DoesNotExist:
                return Response({"error": f"OptionChoice with id {option_id} not found for this item."}, status=status.HTTP_404_NOT_FOUND)

        # সফলভাবে আপডেট করার পর, ক্যাটাগরির সর্বশেষ অবস্থা রিটার্ন করুন
        refreshed_category = self.get_object(user_id, pk)
        serializer = MenuCategorySerializer(refreshed_category)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class CartViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    """
    GET /api/cart/
    PATCH /api/cart/
    """
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def list(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user).select_related('menu_item').prefetch_related('selected_options')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddCartItemSerializer
        if self.request.method == 'PATCH':
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return {'cart': cart, 'request': self.request}

    @action(detail=True, methods=['post'])
    def increase_quantity(self, request, pk=None):
        """ একটি নির্দিষ্ট কার্ট আইটেমের পরিমাণ ১ বাড়ায়। """
        cart_item = self.get_object()
        cart_item.increase_quantity()
        return Response({'status': 'quantity increased'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def decrease_quantity(self, request, pk=None):
        """ একটি নির্দিষ্ট কার্ট আইটেমের পরিমাণ ১ কমায়। """
        cart_item = self.get_object()
        cart_item.decrease_quantity()
    
        if not CartItem.objects.filter(pk=pk).exists():
            return Response({'status': 'item removed'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'status': 'quantity decreased'}, status=status.HTTP_200_OK)
    


# ---------------------For Mollie Payment gateway ------------------------------
# discover/views.py

# discover/views.py

import logging
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from mollie.api.client import Client
from mollie.api.error import UnprocessableEntityError, Error as MollieApiError

logger = logging.getLogger(__name__)

class CreatePaymentView(APIView):
    """
    Mollie-এর মাধ্যমে একটি পেমেন্ট তৈরি করার জন্য একটি API ভিউ।
    """
    def post(self, request, *args, **kwargs):
        try:
            mollie_client = Client()
            mollie_client.set_api_key(settings.MOLLIE_API_KEY)
        except Exception as e:
            logger.error(f"Mollie API কী লোড করতে ব্যর্থ: {e}")
            return Response(
                {'error': 'পেমেন্ট সিস্টেম কনফিগারেশনে সমস্যা হয়েছে।'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        amount = request.data.get('amount')
        description = request.data.get('description')

        if amount is None:
            return Response({'error': 'Amount is a required field.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            formatted_amount = f"{float(amount):.2f}"
        except (ValueError, TypeError):
            return Response({'error': 'Invalid amount provided. Please send a valid number.'}, status=status.HTTP_400_BAD_REQUEST)

        payment_data = {
            'amount': {'currency': 'EUR', 'value': formatted_amount},
            'description': description or 'Qoupon Project Payment',
            'redirectUrl': 'https://your-frontend-app.com/payment-success/',
            'webhookUrl': 'https://your-backend-domain.com/discover/mollie-webhook/',
        }

        try:
            # Mollie API ব্যবহার করে পেমেন্ট তৈরি করুন
            payment = mollie_client.payments.create(payment_data)

            # --- আসল সমাধান এখানে ---
            # payment.checkout_url ব্যবহার করুন, এটি সবচেয়ে নিরাপদ
            checkout_url = payment.checkout_url

            # সফলভাবে পেমেন্ট তৈরি হলে চেকআউট URL রিটার্ন করুন
            return Response(
                {'checkout_url': checkout_url},
                status=status.HTTP_201_CREATED
            )

        except UnprocessableEntityError as e:
            logger.error(f"Mollie UnprocessableEntityError: {e}")
            return Response({'error': f'Payment data is invalid. Details: {e.detail}'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        except MollieApiError as e:
            logger.error(f"Mollie API Error: {e}")
            return Response({'error': 'Could not connect to the payment provider. Please check API key or network.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        except Exception as e:
            # --- বিস্তারিত লগিং যোগ করা হয়েছে ---
            # এই লগটি আপনাকে টার্মিনালে আসল এরর দেখাবে
            logger.error(f"An unexpected error occurred after payment creation: {e}", exc_info=True)
            return Response(
                {'error': 'An unexpected error occurred. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReviewMenuItemViewSet(ModelViewSet):

    queryset = ReviewMenuItem.objects.all()
    serializer_class = ReviewMenuItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReviewMenuItem.objects.filter(user=self.request.user)



class FAQListView(APIView):
    def get(self, request, format=None):
        faqs = FAQ.objects.all()
        serializer = FAQSerializer(faqs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class MyReviewListView(ListAPIView):
    serializer_class = ReviewMenuItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReviewMenuItem.objects.filter(user=self.request.user).order_by('-created_at')