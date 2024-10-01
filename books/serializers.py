# Defining for Book, Author and UserFavorites
from rest_framework import serializers
from .models import Book, Author, UserFavorites

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'

class BookSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all())

    class Meta:
        model = Book
        fields = '__all__'

class UserFavoritesSerializer(serializers.ModelSerializer):

    # Using primaryKeyRelated Field to allow books to be passed by their IDs
    # favorites = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all(), many=True, required=False)
    favorites = BookSerializer(many=True, read_only=True)  # Change this to use BookSerializer

    class Meta:
        model = UserFavorites
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}