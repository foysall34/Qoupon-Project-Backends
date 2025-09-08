
from rest_framework import generics, permissions
from .models import Business_profile , Business_profile_Category
from .serializers import Business_profile_Serializer,Categories_Serializer ,BusinessProfileCategorySerializer,ImageSerializer
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from rest_framework.filters import SearchFilter
from rest_framework .permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

class CreateStoreView(generics.CreateAPIView):
    queryset = Business_profile.objects.all()
    serializer_class = Business_profile_Serializer
    permission_classes = [permissions.IsAuthenticated]

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
        """
        """
        user = self.request.user
        if user.is_staff: 
            return super().get_queryset() 
        return Create_Deal.objects.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        """
        """
        serializer.save(user=self.request.user)
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
            # সফলভাবে আপলোড হলে HTTPS URL সহ প্রতিক্রিয়া পাঠান
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)