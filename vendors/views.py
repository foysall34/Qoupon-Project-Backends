
from rest_framework import generics, permissions
from django.db import models

from food.models import Profile
from food.serializers import ProfileSerializer
from .models import Business_profile , Business_profile_Category, WishDeal
from .serializers import Business_profile_Serializer,Categories_Serializer ,BusinessProfileCategorySerializer,ImageSerializer, WishDealSerializer, FollowerSerializer
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from rest_framework.filters import SearchFilter
from rest_framework .permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404 
from subscription.models import Subscription


class AllBusinessProfilesListView(generics.ListAPIView):
    queryset = Business_profile.objects.all()
    serializer_class = Business_profile_Serializer


class CreateStoreView(generics.ListCreateAPIView):
    queryset = Business_profile.objects.all()
    serializer_class = Business_profile_Serializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Business_profile.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        
       
        custom_response_data = {
            "message": "Business profile created successfully.",
            "data": serializer.data 
        }
        
        return Response(custom_response_data, status=status.HTTP_201_CREATED, headers=headers)
    

# For PATCH METHOD & UPDATE METHOD 


class CreateStoreViewPatch(generics.RetrieveUpdateAPIView):
   
    serializer_class = Business_profile_Serializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        
        queryset = Business_profile.objects.filter(owner=self.request.user)
        # get_object_or_404 ব্যবহার করে নিশ্চিত করা হচ্ছে যে ব্যবহারকারীর একটি প্রোফাইল আছে
        # যদি না থাকে, তাহলে 404 Not Found এরর আসবে।
        obj = get_object_or_404(queryset)
        return obj

    def update(self, request, *args, **kwargs):
        """
        PATCH/PUT রিকোয়েস্টের জন্য কাস্টম রেসপন্স ফরম্যাট তৈরি করে।
        """
        partial = kwargs.pop('partial', True) # PATCH এর জন্য partial=True সেট করা হলো
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        custom_response_data = {
            "message": "Your business profile has been updated successfully.",
            "data": serializer.data
        }

        return Response(custom_response_data, status=status.HTTP_200_OK)

from rest_framework import viewsets, parsers
from .models import Deal, Vendor_Category
from .serializers import DealSerializer, CategorySerializer

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows categories to be viewed or edited.
    Provides data for the 'Category' dropdown in the app.
    """
    queryset = Vendor_Category.objects.all()
    serializer_class = CategorySerializer


class DealViewSet(viewsets.ModelViewSet):
    queryset = Deal.objects.all()
    serializer_class = DealSerializer
    
    def get_queryset(self):
        """
        Optionally restricts the returned deals to a specific user if `user_id` is provided in query params.
        """
        queryset = super().get_queryset() 
        user_id = self.request.query_params.get('user_id', None)
        if user_id is not None:
            queryset = queryset.filter(user__id=user_id)
        return queryset

    def partial_update(self, request, *args, **kwargs):
        """
        Handle partial update (PATCH request) for a deal.
        Allows updating specific fields without requiring all fields.
        """
        # Get the instance to be updated
        instance = self.get_object()

        # Here, we assume that you're sending the fields to be updated in the request body.
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        
        # Check if the serialized data is valid
        if serializer.is_valid():
            # Save the updated instance
            serializer.save()

            # Return the updated instance data in the response
            return Response(serializer.data)
        else:
            # If validation fails, return the errors in the response
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# deals/views.py
from rest_framework import generics, permissions
from .models import Create_Deal, Business_profile
from .serializers import Create_DealSerializer
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend 

  

'''

class CreateDealViewSet(viewsets.ModelViewSet):
    """
    user_id set for the url , so that search by user_id eaily 
    """
    queryset = Create_Deal.objects.all().order_by('-created_at') 
    serializer_class = Create_DealSerializer

    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user']  

    def get_queryset(self):
        user = self.request.user
        if user.is_staff: 
            return super().get_queryset() 
        return Create_Deal.objects.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Deal deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )
'''


from io import BytesIO
from django.core.files.base import ContentFile
import qrcode
from qrcode.constants import ERROR_CORRECT_M

class CreateDealViewSet(viewsets.ModelViewSet):
    """
    Create, update, delete, list deals.
    QR code is generated automatically and saved into qrimage.
    """
    queryset = Create_Deal.objects.all().order_by('-created_at') 
    serializer_class = Create_DealSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user']  

    def get_queryset(self):
        user = self.request.user
        if user.is_staff: 
            return super().get_queryset() 
        return Create_Deal.objects.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        # First save the deal
        deal = serializer.save(user=self.request.user)

        # --- Generate QR code ---
        # 1. Construct QR URL (base + deal id)
        base_url = "https://intensely-optimal-unicorn.ngrok-free.app/vendors/all-deals/"   # <--- replace with your base URL
        qr_data = f"{base_url}{deal.id}/"

        # 2. Generate QR code
        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        # 3. Save image to buffer
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        buffer.seek(0)

        # 4. Save to model field
        filename = f"deal_{deal.id}_qr.png"
        deal.qrimage.save(filename, ContentFile(buffer.read()), save=True)

    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve to increment the view count each time a deal is viewed.
        """
        deal = self.get_object()  # Get the deal by its pk

        # Increment view count
        deal.view_count += 1
        deal.save()

        # Proceed with the default retrieve action
        serializer = self.get_serializer(deal)
        return Response(serializer.data)


# for categories views.py (breakfast , lunch , dinner )
class categoryItemListView(generics.ListAPIView):
    """
    - /api/menu/                        
    - /api/menu/?category=Breakfast    
    - /api/menu/?search=Chicken      
    - /api/menu/?category=Lunch&search=Steak 
    """
    serializer_class = Categories_Serializer
    filter_backends = [SearchFilter]
    search_fields = ['title', 'description']

    def get_queryset(self):
        queryset = Vendor_Category.objects.all()
        category = self.request.query_params.get('category', None)
        if category is not None:
          
            queryset = queryset.filter(category__iexact=category)
            
        return queryset
    
class BusinessProfileCategoryViewSet(viewsets.ModelViewSet):
    queryset = Business_profile_Category.objects.all()
    serializer_class = BusinessProfileCategorySerializer




class ImageUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = ImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class AllDealsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Get the active subscription
        subscription = Subscription.objects.filter(user=user, is_active=True).first()

        # If there's an active subscription, get all deals
        if subscription:
            deals = Create_Deal.objects.all()
            print("User has an active subscription.")
        else:
            # If no active subscription, filter for "Free" or "Both" deals
            deals = Create_Deal.objects.filter(is_active=True, deal_type__in=["Free", "Both"])
            print("User does not have an active subscription.")

        # Check if the user has a business profile and adjust the filtering accordingly
        if hasattr(user, "business_profile"):
            deals = Create_Deal.objects.filter(is_active=True, user=user)
            print("User is a vendor with a business profile. Showing only their deals.")

        # Serialize the filtered deals
        serializer = Create_DealSerializer(deals, many=True, context={"request": request})
        return Response(serializer.data)
    

class AllVendorDealsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Get all active deals
        deals = Create_Deal.objects.filter(is_active=True)
        
        # For better performance, use update to increment all view counts at once
        Create_Deal.objects.filter(is_active=True).update(view_count=models.F('view_count') + 1)
        
        serializer = Create_DealSerializer(deals, many=True, context={"request": request})
        return Response(serializer.data)
    

class ALlDealsDetailsView(APIView):
    def get(self, request, id):
        user = request.user
        if hasattr(user, "subscription") and user.subscription.is_active:
            deals = Create_Deal.objects.get(is_active=True, id=id)
        else:
            deals = Create_Deal.objects.get(is_active=True, deal_type__in=["Free", "Both"], id=id)
        serializer= Create_DealSerializer(deals, context={"request": request})
        return Response(serializer.data)
    

class DealByIDView(APIView):
    permission_classes = [permissions.AllowAny]  

    def get(self, request, id):
        try:
            deal = Create_Deal.objects.get(id=id)
            serializer = Create_DealSerializer(deal)
            return Response(serializer.data)
        except Create_Deal.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

class WishDealListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated] 

    def get(self, request):
        """
        GET: List all wish deals of the authenticated user
        """
        wish_deals = WishDeal.objects.filter(user=request.user)
        serializer = WishDealSerializer(wish_deals, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        POST: Add a new wish deal for the authenticated user and increment the activation field in Create_Deal.
        """
        data = request.data
        data['user'] = request.user.id  # Automatically add the authenticated user's ID
        serializer = WishDealSerializer(data=data)

        if serializer.is_valid():
            # Save the new wish deal
            wish_deal = serializer.save()

            try:
                create_deal = wish_deal.deal  
                
                create_deal.activation += 1  
                create_deal.save() 

                print(f"Updated Create_Deal activation: {create_deal.activation}")

            except Create_Deal.DoesNotExist:
                # Handle the case where the associated Create_Deal is not found
                return Response({"detail": "Associated deal not found."}, status=status.HTTP_404_NOT_FOUND)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        """
        DELETE: Remove a wish deal from the authenticated user's wishlist
        """
        try:
            # Find the wish deal
            wish_deal = WishDeal.objects.get(id=pk, user=request.user)
            wish_deal.delete()
            return Response({"message": "Delete successful"}, status=status.HTTP_204_NO_CONTENT)
        except WishDeal.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        

class VendorDealListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, vendor_id):
        """
        Return all deals created by a given vendor (user).
        """
        deals = Create_Deal.objects.filter(user_id=vendor_id)

        if not deals.exists():
            return Response(
                {"detail": "No deals found for this vendor."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = Create_DealSerializer(deals, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class SendDealNotification(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, deal_id):
        title = request.data.get("title")
        body = request.data.get("body")

        if not title or not body:
            return Response(
                {"detail": "Both 'title' and 'body' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            deal = Create_Deal.objects.get(id=deal_id, user=request.user)
        except Create_Deal.DoesNotExist:
            return Response(
                {"detail": "Deal not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Build deal data payload
        deal_data = {
            "deal_id": str(deal.id),
            "title": deal.title,
            "discount_value": str(deal.discount_value),
            "type": "new_deal"
        }

        # Exclude vendor users (those with a business profile)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        non_vendor_users = User.objects.exclude(
            id__in=Business_profile.objects.values_list('owner_id', flat=True)
        )

        # Send notifications
        success_count = 0
        for user in non_vendor_users:
            from notifications.utils import FirebaseNotification
            if FirebaseNotification.send_to_user(
                user=user,
                title=title,
                body=body,
                data=deal_data,
                notification_type="promotion"
            ):
                success_count += 1

        return Response(
            {
                "detail": f"Notifications sent to {success_count} users.",
                "deal_id": deal.id,
                "sent": success_count > 0
            },
            status=status.HTTP_200_OK
        )
        


# 1️⃣ Follow a vendor
class FollowVendorAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, vendor_id):
        try:
            vendor = Business_profile.objects.get(id=vendor_id)
        except Business_profile.DoesNotExist:
            return Response({"error": "Vendor not found"}, status=status.HTTP_404_NOT_FOUND)

        vendor.followers.add(request.user)
        return Response({"message": "Successfully followed vendor"}, status=status.HTTP_200_OK)


# 2️⃣ Unfollow a vendor
class UnfollowVendorAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, vendor_id):
        try:
            vendor = Business_profile.objects.get(id=vendor_id)
        except Business_profile.DoesNotExist:
            return Response({"error": "Vendor not found"}, status=status.HTTP_404_NOT_FOUND)

        vendor.followers.remove(request.user)
        return Response({"message": "Successfully unfollowed vendor"}, status=status.HTTP_200_OK)


# 3️⃣ Get List of Followed Vendors of a Customer
class FollowedVendorsListAPIView(generics.ListAPIView):
    serializer_class = Business_profile_Serializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.followed_vendors.all()


# 4️⃣ Get List of Customers that Follow Me (as Vendor)
from rest_framework import generics, permissions
from django.db.models import Prefetch

class VendorFollowersListAPIView(generics.ListAPIView):
    # Use your existing Profile serializer so you return Profile fields
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]  # needs the vendor user

    def get_queryset(self):
        # Locate the vendor's business profile(s)
        business = (
            Business_profile.objects
            .filter(owner=self.request.user)
            .first()
        )

        if not business:
            return Profile.objects.none()

        # Users who follow this vendor
        follower_users_qs = business.followers.all().only('id')  # cheaper

        # Return Profile rows for those users
        # (adjust select_related/prefetch to your Profile model fields)
        return (
            Profile.objects
            .filter(user__in=follower_users_qs)
            .select_related('user')  # if Profile has OneToOne to User
        )
