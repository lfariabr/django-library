from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Author(models.Model):
    name = models.CharField(max_length=255)
    ratings_count = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    text_reviews_count = models.IntegerField(default=0)
    works_count = models.IntegerField(default=0)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    fans_count = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=100, db_index=True) # for performance optimization
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    work_id = models.CharField(max_length=255, unique=True)
    book_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        
        return self.title

class UserFavorites(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    favorites = models.ManyToManyField(Book, related_name='favorited_by')

    def __str__(self):
        return f"{self.user}'s favorite books"