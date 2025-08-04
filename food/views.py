from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import FoodCategory, UserProfile
from .serializers import FoodCategorySerializer, UserProfileCreateSerializer , UserProfileDetailSerializer
from .models import Place
from .serializers import PlaceSerializer

@api_view(['GET', 'POST'])
def food_category_list(request):

    # GET অনুরোধের জন্য সকল ক্যাটাগরির তালিকা পাঠানো হবে
    if request.method == 'GET':
        categories = FoodCategory.objects.all()
        serializer = FoodCategorySerializer(categories, many=True)
        return Response(serializer.data)

    # POST অনুরোধের জন্য নতুন ক্যাটাগরি তৈরি করা হবে
    elif request.method == 'POST':
        serializer = FoodCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


User = get_user_model()

@api_view(['POST'])
def create_user_profile(request):
    """
    POST: একটি নতুন ইউজার প্রোফাইল তৈরি করে।
    """
    serializer = UserProfileCreateSerializer(data=request.data)
    if serializer.is_valid():
        profile = serializer.save()
        # সফলভাবে তৈরি হওয়ার পর, বিস্তারিত দেখানোর জন্য অন্য সিরিয়ালাইজার ব্যবহার করা হচ্ছে
        response_serializer = UserProfileDetailSerializer(profile)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_user_profile(request, email):
    """
    GET: নির্দিষ্ট ইমেইলের ইউজারের প্রোফাইল দেখায়।
    """
    try:
        user = User.objects.get(email=email)
        profile = UserProfile.objects.get(user=user)
        serializer = UserProfileDetailSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"error": f"User with email '{email}' not found."}, status=status.HTTP_404_NOT_FOUND)
    except UserProfile.DoesNotExist:
        return Response({"error": f"Profile for user with email '{email}' not found."}, status=status.HTTP_404_NOT_FOUND)
    



# Google Map Intregation
# --- সকল স্থান দেখা এবং নতুন স্থান তৈরি করার জন্য ভিউ ---
@api_view(['GET', 'POST'])
def place_list(request):
    """
    GET: সকল স্থানের একটি তালিকা দেখায়।
    POST: একটি নতুন স্থান তৈরি করে।
    """
    if request.method == 'GET':
        places = Place.objects.all().order_by('-created_at')
        serializer = PlaceSerializer(places, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = PlaceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- একটি নির্দিষ্ট স্থান দেখা, আপডেট এবং ডিলিট করার জন্য ভিউ ---
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def place_detail(request, pk):
    """
    GET: একটি নির্দিষ্ট স্থান দেখায়।
    PUT/PATCH: একটি নির্দিষ্ট স্থান আপডেট করে।
    DELETE: একটি নির্দিষ্ট স্থান ডিলিট করে।
    """
    try:
        place = Place.objects.get(pk=pk)
    except Place.DoesNotExist:
        return Response({"error": "স্থান খুঁজে পাওয়া যায়নি।"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = PlaceSerializer(place)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        # partial=True দিলে PATCH অনুরোধ সঠিকভাবে কাজ করবে
        serializer = PlaceSerializer(instance=place, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        place.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)