
from rest_framework import generics, permissions
from .models import Business_profile
from .serializers import Business_profile_Serializer
from rest_framework.response import Response
from rest_framework import generics, permissions, status
class CreateStoreView(generics.CreateAPIView):
    queryset = Business_profile.objects.all()
    serializer_class = Business_profile_Serializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # owner হিসেবে বর্তমান ব্যবহারকারীকে সেট করা হচ্ছে
        serializer.save(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        # প্রথমে ডিফল্ট create মেথডের কাজগুলো সম্পন্ন করা হচ্ছে
        # (যেমন: ভ্যালিডেশন এবং perform_create কল করা)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # ডিফল্ট হেডার পাওয়া যাচ্ছে
        headers = self.get_success_headers(serializer.data)
        
        # কাস্টম রেসপন্স তৈরি করা হচ্ছে
        custom_response_data = {
            "message": "Business profile created successfully.",
            "data": serializer.data  # নতুন তৈরি হওয়া প্রোফাইলের ডেটা
        }
        
        return Response(custom_response_data, status=status.HTTP_201_CREATED, headers=headers)