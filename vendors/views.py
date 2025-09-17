
from rest_framework import generics, permissions
from .models import Business_profile , Business_profile_Category
from .serializers import Business_profile_Serializer,Categories_Serializer ,BusinessProfileCategorySerializer,ImageSerializer
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from rest_framework.filters import SearchFilter
from rest_framework .permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404 

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
from .models import Deal, Vendor_Category, ModifierGroup
from .serializers import DealSerializer, CategorySerializer, ModifierGroupSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows categories to be viewed or edited.
    Provides data for the 'Category' dropdown in the app.
    """
    queryset = Vendor_Category.objects.all()
    serializer_class = CategorySerializer

class ModifierGroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows modifier groups to be viewed or edited.
    Provides data for the 'Choose Modifier Groups' dropdown.
    """
    queryset = ModifierGroup.objects.all()
    serializer_class = ModifierGroupSerializer

class DealViewSet(viewsets.ModelViewSet):
 
    queryset = Deal.objects.all() 
    serializer_class = DealSerializer
    
    def get_queryset(self):
        """
        """
        queryset = super().get_queryset() 
        user_id = self.request.query_params.get('user_id', None)
        if user_id is not None:
            queryset = queryset.filter(user__id=user_id)
        return queryset



# deals/views.py
from rest_framework import generics, permissions
from .models import Create_Deal, Business_profile
from .serializers import Create_DealSerializer
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend 

  



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