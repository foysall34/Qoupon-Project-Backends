from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import FoodCategory, Fvt_category
from .serializers import FoodCategorySerializer , UserFvtDetailSerializer ,  ProfileSerializer
from .models import Place , Profile
from .serializers import PlaceSerializer 
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny


from rest_framework_simplejwt.authentication import JWTAuthentication 

@api_view(['GET', 'POST'])
def food_category_list(request):
    if request.method == 'GET':
        categories = FoodCategory.objects.all()
        serializer = FoodCategorySerializer(categories, many=True)
        return Response(serializer.data)

   
    elif request.method == 'POST':
        serializer = FoodCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


User = get_user_model()


@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([AllowAny])
def manage_my_favorite_categories(request):
    
    current_user = request.user


    if request.method == 'GET':
        try:
            fvt_profile = Fvt_category.objects.get(user=current_user)
        except Fvt_category.DoesNotExist:
            return Response(
                {"error": f"Favorite profile for user '{current_user.email}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserFvtDetailSerializer(fvt_profile)
        
       
        response_data = {
            "user_email": serializer.data['user_info']['email'],
            "user_favorite_categories": [category['name'] for category in serializer.data['favorite_categories']],
            "success_msg": "Successfully retrieved your favorite categories."
        }
        return Response(response_data, status=status.HTTP_200_OK)

   
    elif request.method == 'POST':
        category_names = request.data.get('favorite_category_names', [])

        if not isinstance(category_names, list):
            return Response(
                {"error": "favorite_category_names must be a list of strings."},
                status=status.HTTP_400_BAD_REQUEST
            )

        categories_to_set = []
        missing_categories = []
        for name in category_names:
            try:
                category = FoodCategory.objects.get(name__iexact=name.strip())
                categories_to_set.append(category)
            except FoodCategory.DoesNotExist:
                missing_categories.append(name)

        if missing_categories:
            return Response(
                {"error": f"These categories were not found: {', '.join(missing_categories)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        profile, created = Fvt_category.objects.get_or_create(user=current_user)
        profile.favorite_categories.set(categories_to_set)

        serializer = UserFvtDetailSerializer(profile)
    
        response_data = {
            "user_email": serializer.data['user_info']['email'],
            "user_favorite_categories": [category['name'] for category in serializer.data['favorite_categories']],
            "success_msg": "Successfully updated your favorite categories."
        }
        
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        
        return Response(response_data, status=response_status)

 
    



# Google Map Intregation

@api_view(['GET', 'POST'])
def place_list(request):
   
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


# --- see specific place ---
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def place_detail(request, pk):
    
    try:
        place = Place.objects.get(pk=pk)
    except Place.DoesNotExist:
        return Response({"error": "স্থান খুঁজে পাওয়া যায়নি।"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = PlaceSerializer(place)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
      
        serializer = PlaceSerializer(instance=place, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        place.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    


# For profile page api 

@api_view(['GET', 'POST', 'PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def user_profile_view(request):
   
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    elif request.method in ['PUT', 'POST']:
        serializer = ProfileSerializer(profile, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": f"Profile successfully updated .",
                "data": serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)