
from rest_framework import generics, permissions
from .models import Business_profile
from .serializers import Business_profile_Serializer,Categories_Serializer
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from rest_framework.filters import SearchFilter

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
    """
    API endpoint for creating, viewing, and editing Deals.
    """
    queryset = Deal.objects.all().order_by('-created_at')
    serializer_class = DealSerializer
 
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]





# deals/views.py

from rest_framework import generics, permissions
from .models import Create_Deal, Business_profile
from .serializers import Create_DealSerializer
from rest_framework.views import APIView

  

class CreateDealListCreateView(APIView):
    """
    এই ভিউটি সমস্ত ডিল লিস্ট করার জন্য (GET) এবং একটি নতুন ডিল তৈরি করার জন্য (POST) ব্যবহৃত হবে।
    """

    def get(self, request, format=None):
        """
        ডাটাবেস থেকে সমস্ত 'Create_Deal' অবজেক্ট নিয়ে আসে এবং তা লিস্ট হিসেবে রিটার্ন করে।
        """
        try:
            deals = Create_Deal.objects.all()
            serializer = Create_DealSerializer(deals, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, format=None):
        """
        একটি নতুন 'Create_Deal' এবং এর সাথে সম্পর্কিত 'DeliveryCost' অবজেক্ট তৈরি করে।
        """
        serializer = Create_DealSerializer(data=request.data)
        
        # ডেটা ভ্যালিড কিনা তা পরীক্ষা করা হচ্ছে
        if serializer.is_valid():
            # যদি ভ্যালিড হয়, তাহলে serializer-এর create() মেথড কল হবে
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        # যদি ডেটা ভ্যালিড না হয়, তাহলে error রিটার্ন করবে
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateDealDetailView(APIView):
    """
    একটি নির্দিষ্ট ডিল পুনরুদ্ধার (retrieve), আপডেট (update) বা ডিলিট (delete) করে।
    """
    def get_object(self, pk):
        try:
            return Create_Deal.objects.get(pk=pk)
        except Create_Deal.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        deal = self.get_object(pk)
        serializer = Create_DealSerializer(deal)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        একটি ডিলকে সম্পূর্ণভাবে আপডেট করে। সব 필্ড সরবরাহ করতে হবে।
        """
        deal = self.get_object(pk)
        serializer = Create_DealSerializer(instance=deal, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        """
        একটি ডিলকে আংশিকভাবে আপডেট করে। শুধুমাত্র যে 필্ডগুলো পরিবর্তন করতে হবে, সেগুলো সরবরাহ করলেই হবে।
        """
        deal = self.get_object(pk)
        # partial=True প্যারামিটারটি PATCH রিকোয়েস্টের জন্য আবশ্যক
        serializer = Create_DealSerializer(instance=deal, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        deal = self.get_object(pk)
        deal.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

# for categories views.py (breakfast , lunch , dinner )
class categoryItemListView(generics.ListAPIView):
    """
    এই ভিউটি মেনু আইটেমগুলোর একটি তালিকা প্রদান করে।
    এটি 'category' অনুযায়ী ফিল্টার এবং 'search' অনুযায়ী সার্চ সমর্থন করে।
    
    ব্যবহারের উদাহরণ:
    - /api/menu/                          -> সমস্ত আইটেম দেখাবে
    - /api/menu/?category=Breakfast       -> শুধুমাত্র ব্রেকফাস্ট আইটেম দেখাবে
    - /api/menu/?search=Chicken           -> 'Chicken' শব্দটি দিয়ে আইটেম খুঁজবে
    - /api/menu/?category=Lunch&search=Steak -> লাঞ্চের মধ্যে 'Steak' দিয়ে খুঁজবে
    """
    serializer_class = Categories_Serializer
    
    # সার্চিং এর জন্য filter backend এবং কোন কোন ফিল্ডে সার্চ হবে তা নির্ধারণ
    filter_backends = [SearchFilter]
    search_fields = ['title', 'description']

    def get_queryset(self):
        """
        এই মেথডটি URL-এর query parameter চেক করে queryset-কে ফিল্টার করে।
        """
        # প্রথমে সমস্ত অবজেক্ট নিয়ে আসা হয়
        queryset = Vendor_Category.objects.all()
        
        # URL থেকে 'category' প্যারামিটারটি নেওয়া হচ্ছে
        category = self.request.query_params.get('category', None)
        
        # যদি 'category' প্যারামিটার থাকে, তাহলে queryset-কে সেই অনুযায়ী ফিল্টার করা হবে
        if category is not None:
            # category__iexact ব্যবহার করলে case-insensitive (ছোট/বড় হাতের অক্ষর) ম্যাচিং হবে
            queryset = queryset.filter(category__iexact=category)
            
        return queryset