
from rest_framework import generics, permissions
from .models import Business_profile , Business_profile_Category
from .serializers import Business_profile_Serializer,Categories_Serializer ,BusinessProfileCategorySerializer
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from rest_framework.filters import SearchFilter
from rest_framework .permissions import IsAuthenticated


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
    # এই লাইনটি যোগ করুন
    queryset = Deal.objects.all() 
    serializer_class = DealSerializer
    
    def get_queryset(self):
        """
        এই মেথডটি বেস queryset-কে ফিল্টার করবে।
        """
        # queryset = Deal.objects.all() লাইনটিকে এখানে self.queryset দিয়ে পরিবর্তন করুন
        queryset = super().get_queryset() # অথবা queryset = self.queryset 
        
        # URL থেকে 'user_id' প্যারামিটারটি খোঁজা হচ্ছে
        user_id = self.request.query_params.get('user_id', None)
        
        if user_id is not None:
            # যদি user_id পাওয়া যায়, তাহলে queryset-কে ফিল্টার করা হচ্ছে
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
    একটি ViewSet যা Create_Deal অবজেক্ট দেখা, তৈরি করা, আপডেট করা এবং ডিলিট করার সুবিধা দেয়।
    URL-এ user=<id> প্যারামিটার ব্যবহার করে নির্দিষ্ট ইউজারের তৈরি করা ডিল ফিল্টার করা যাবে।
    """
    
    # 1. বেস কোয়েরিসেট এবং সিরিয়ালাইজার ক্লাস নির্ধারণ
    queryset = Create_Deal.objects.all().order_by('-created_at') # সব ডিল আনা হচ্ছে এবং নতুনগুলো আগে দেখানো হচ্ছে
    serializer_class = Create_DealSerializer
    
    # 2. অনুমতি (Permissions) সেট করা
    # শুধুমাত্র প্রমাণীকৃত (authenticated) ইউজাররাই এই API অ্যাক্সেস করতে পারবে
    permission_classes = [IsAuthenticated]
    
    # 3. ফিল্টারিং কনফিগারেশন
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user']  # 'user' ফিল্ডের ID দিয়ে ফিল্টার করার সুবিধা যোগ করা হলো

    def get_queryset(self):
        """
        শুধুমাত্র লগইন করা ইউজারকে তার নিজের তৈরি করা ডিলগুলো দেখানোর জন্য এই মেথডটি ওভাররাইড করা যেতে পারে।
        তবে অ্যাডমিন সব দেখতে পারবে।
        """
        user = self.request.user
        if user.is_staff: # যদি ইউজার অ্যাডমিন বা স্টাফ হয়
            return super().get_queryset() # সব ডিল দেখানো হবে
        
        # সাধারণ ইউজার হলে শুধুমাত্র তার নিজের ডিলগুলো দেখানো হবে
        return Create_Deal.objects.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        """
        নতুন ডিল তৈরি করার সময় রিকোয়েস্ট পাঠানো ইউজারকে স্বয়ংক্রিয়ভাবে 'user' ফিল্ডে সেট করে।
        এটি સુરક્ષার জন্য জরুরি, যাতে কোনো ইউজার অন্য ইউজারের নামে ডিল তৈরি করতে না পারে।
        """
        serializer.save(user=self.request.user)
# for categories views.py (breakfast , lunch , dinner )



class categoryItemListView(generics.ListAPIView):
    """
   
  
    
    ব্যবহারের উদাহরণ:
    - /api/menu/                        
    - /api/menu/?category=Breakfast    
    - /api/menu/?search=Chicken      
    - /api/menu/?category=Lunch&search=Steak 
    """
    serializer_class = Categories_Serializer
    
    # সার্চিং এর জন্য filter backend এবং কোন কোন ফিল্ডে সার্চ হবে তা নির্ধারণ
    filter_backends = [SearchFilter]
    search_fields = ['title', 'description']

    def get_queryset(self):
        """
        এই মেথডটি URL-এর query parameter চেক করে queryset-কে ফিল্টার করে।
        """
     
        queryset = Vendor_Category.objects.all()
        
       
        category = self.request.query_params.get('category', None)
        
      
        if category is not None:
          
            queryset = queryset.filter(category__iexact=category)
            
        return queryset
    


class BusinessProfileCategoryViewSet(viewsets.ModelViewSet):
    queryset = Business_profile_Category.objects.all()
    serializer_class = BusinessProfileCategorySerializer