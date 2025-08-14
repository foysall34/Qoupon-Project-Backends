# api/filters.py

from django_filters import rest_framework as filters
from .models import Restaurant, Cuisine, Diet

class RestaurantFilter(filters.FilterSet):
    # রেটিং অনুযায়ী ফিল্টার (e.g., ?rating_min=4)
    rating_min = filters.NumberFilter(field_name="rating", lookup_expr='gte')

    # কুইজিন অনুযায়ী ফিল্টার (e.g., ?cuisines=American)
    # এখানে to_field_name='name' ব্যবহার করায় আমরা ID এর বদলে নাম দিয়ে ফিল্টার করতে পারব।
    cuisines = filters.ModelMultipleChoiceFilter(
        queryset=Cuisine.objects.all(),
        field_name='cuisines__name',
        to_field_name='name',
    )
    
    # ডায়েট অনুযায়ী ফিল্টার (e.g., ?diets=Vegan)
    diets = filters.ModelMultipleChoiceFilter(
        queryset=Diet.objects.all(),
        field_name='diets__name',
        to_field_name='name',
    )

    # দামের রেঞ্জ অনুযায়ী ফিল্টার
    PRICE_CHOICES = (
        ('less_30', 'Less than $30'),
        ('30_40', '$30 - $40'),
        ('40_more', '$40 or more'),
    )
    price_range = filters.ChoiceFilter(
        label='Price Range',
        choices=PRICE_CHOICES,
        method='filter_by_price_range' # কাস্টম লজিকের জন্য মেথড
    )

    class Meta:
        model = Restaurant
        fields = ['cuisines', 'diets', 'rating_min', 'price_range']

    def filter_by_price_range(self, queryset, name, value):
        if value == 'less_30':
            return queryset.filter(average_price__lt=30)
        elif value == '30_40':
            return queryset.filter(average_price__gte=30, average_price__lte=40)
        elif value == '40_more':
            return queryset.filter(average_price__gt=40)
        return queryset