from django.db import models
from cloudinary.models import CloudinaryField




class Cuisine(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Diet(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name






class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    # models.ImageField এর পরিবর্তে CloudinaryField ব্যবহার করা হয়েছে
    logo = CloudinaryField('image', blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    review_count = models.CharField(max_length=20, default="500+")
    distance_km = models.DecimalField(max_digits=4, decimal_places=1)
    tags = models.CharField(max_length=255, help_text="Comma-separated tags e.g., Vegan, Gezond, Pizza")
    discount_percentage = models.IntegerField(default=0)
    cuisines = models.ManyToManyField(Cuisine, related_name='restaurants')
    diets = models.ManyToManyField(Diet, related_name='restaurants')
    average_price = models.DecimalField(max_digits=6, decimal_places=2, help_text="Average price for one person" , blank=True , null= True)

    def __str__(self):
        return self.name
    
