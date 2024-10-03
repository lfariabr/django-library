from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from .models import Book, Author, UserFavorites
from .serializers import BookSerializer, AuthorSerializer, UserFavoritesSerializer
from rest_framework.decorators import action, api_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from books.recommendation.recommendation_engine import get_recommendations
import pandas as pd
import pickle

import os
from django.conf import settings

# Safely load precomputed data if it exists
pkl_dir = settings.BASE_DIR  # Using Django's BASE_DIR for file paths

try:
    with open(os.path.join(pkl_dir, 'tfidf_matrix_10k.pkl'), 'rb') as f:
        tfidf_matrix = pickle.load(f)

    with open(os.path.join(pkl_dir, 'cosine_sim_matrix_10k.pkl'), 'rb') as f:
        cosine_sim_matrix = pickle.load(f)

    with open(os.path.join(pkl_dir, 'df_books_10k.pkl'), 'rb') as f:
        df_books = pickle.load(f)

except FileNotFoundError:
    tfidf_matrix, cosine_sim_matrix, df_books = None, None, None
    print("Precomputed files not found. Run the precompute script first.")

# Loading precomputed data once during app initialization
# with open('tfidf_matrix.pkl', 'rb') as f:
#     tfidf_matrix = pickle.load(f)

# with open('cosine_sim_matrix.pkl', 'rb') as f:
#     cosine_sim_matrix = pickle.load(f)

# with open('df_books.pkl', 'rb') as f:
#     df_books = pickle.load(f)

# Create your views here.
class CustomPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 100

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['title', 'author__name']
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super().get_permissions()

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super().get_permissions()

class UserFavoritesViewSet(viewsets.ModelViewSet):
    queryset = UserFavorites.objects.all()
    serializer_class = UserFavoritesSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return UserFavorites.objects.filter(user=self.request.user).order_by('id')
        else:
            return UserFavorites.objects.none()  # Return an empty queryset if the user is not authenticated
    
    def perform_create(self, serializer):
        # automatically set the user field to current logged user
        user_favorites, created = UserFavorites.objects.get_or_create(user=self.request.user)
        serializer.save(user=self.request.user)
    
    # Listing Favorites
    @action(detail=False, methods=['GET'])
    def list_favorites(self, request):
        user_favorites = UserFavorites.objects.filter(user=request.user)
        page = self.paginate_queryset(user_favorites)
        if page is not None:
            serializer = UserFavoritesSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = UserFavoritesSerializer(user_favorites, many=True)
        return Response(serializer.data)

    # Adding Favorites    
    @action(detail=False, methods=['POST'])
    def add_favorite(self, request):
        # Receiving this of books
        book_ids = request.data.get('book_ids', [])

        # Check to make sure we have ID
        if not book_ids:
            return Response({'status': 'No books provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Making sure 1 request x user
        user_favorites, _ = UserFavorites.objects.get_or_create(user=request.user)

        # Filtering
        books = Book.objects.filter(id__in=book_ids)

        # Checking if books are found on db
        if not books.exists():
            return Response({'status': 'No books found with the provided IDs'}, status=status.HTTP_400_BAD_REQUEST)

        # checking limits
        if user_favorites.favorites.count() + books.count() >= 20:
            return Response({'status': 'Maximum number of books reached'}, status=status.HTTP_400_BAD_REQUEST)

        # Adding new books
        user_favorites.favorites.add(*books)

        # Return response
        return Response({
            'status': f'{books.count()} books added to favorites!',
            'favorites': [book.title for book in user_favorites.favorites.all()]
        }, status=status.HTTP_201_CREATED)
        

    # Removing Favorites
    @action(detail=False, methods=['POST'])
    def remove_favorite(self, request):
        book_id = request.data.get('book_id')

        if not book_id:
            return Response({'status': 'No book ID provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({'status': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

        user_favorites, _ = UserFavorites.objects.get_or_create(user=request.user)
        user_favorites.favorites.remove(book)

        return Response({'status': 'Book removed from favorites!'}, status=status.HTTP_200_OK)
    
    # Clear all Favorites
    @action(detail=False, methods=['POST'])
    def clear_favorites(self, request):
        # Fetch the first UserFavorites record for the user
        user_favorites = UserFavorites.objects.filter(user=request.user).first()
        
        if user_favorites:
            user_favorites.favorites.clear()  # This will remove all favorite books
            return Response({'status': 'All favorites cleared successfully!'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'No favorites to clear!'}, status=status.HTTP_400_BAD_REQUEST)

    # Recommendations based on favorites
    # UPGRADES: 
    # 1) sklearn for content-based filtering (TfidVectorizer and cosine_similarity)
    # 2) scikit-surprise for collaborative filtering (KNNBasic)
    ### VERSION 1
    # @action(detail=False, methods=['GET'])
    # def recommendations(self, request):
        
    #     # Getting user favorites
    #     user_favorites, _ = UserFavorites.objects.get_or_create(user=request.user)
    #     favorite_books = user_favorites.favorites.all()

    #     print("Favorites: ", favorite_books)

    #     # Getting a list of authors of the user's favorite books
    #     favorite_authors = set(book.author for book in favorite_books)
    #     # Recommend books bys these authors... that were not added to favorites yet
    #     recommended_books = Book.objects.filter(author__in=favorite_authors).exclude(id__in=favorite_books.values_list('id', flat=True))[:5]
    #     print("Recommended: ", recommended_books)

    #     if not recommended_books.exists():
    #         return Response({'status': 'No recommendations found'}, status=status.HTTP_404_NOT_FOUND)
    #     # Serializing the recommended books
    #     serializer = BookSerializer(recommended_books, many=True)
    #     return Response(serializer.data)
    
    ### VERSION 2
    # Loading df_books
    # def load_books_from_db(self):
    #     books = Book.objects.all().values()
    #     return pd.DataFrame(books)
    
    # @action(detail=False, methods=['GET'])
    # def recommendations(self, request):
    #     # Load the books DataFrame

    #     df_books = self.load_books_from_db()  # Use self to call the method
        
    #     # Getting user favorites
    #     user_favorites, _ = UserFavorites.objects.get_or_create(user=request.user)
    #     favorite_books = user_favorites.favorites.all()

    #     if not favorite_books.exists():
    #         return Response({'status': 'No favorite books found'}, status=status.HTTP_404_NOT_FOUND)

    #     # Recommend books based on the first favorite book (or adjust as needed)
    #     favorite_book = favorite_books.first()

    #     # Use the get_recommendations function based on the book's title
    #     # recommended_titles = get_recommendations(favorite_book.title)
    #     recommended_titles = get_recommendations(favorite_book.title, df_books=df_books)

    #     # Fetch the recommended books from the database
    #     recommended_books = Book.objects.filter(title__in=recommended_titles).exclude(id__in=favorite_books.values_list('id', flat=True))
        
    #     if not recommended_books.exists():
    #         return Response({'status': 'No recommendations found'}, status=status.HTTP_404_NOT_FOUND)

    #     # Serializing the recommended books
    #     serializer = BookSerializer(recommended_books, many=True)
    #     return Response(serializer.data)
    
    #### VERSION 3 - PRE COMPUTED MATRIX
    @action(detail=False, methods=['GET'])
    def recommendations(self, request):
        user_favorites, _ = UserFavorites.objects.get_or_create(user=request.user)
        favorite_books = user_favorites.favorites.all()

        if not favorite_books.exists():
            return Response({'status': 'No favorite books found'}, status=status.HTTP_404_NOT_FOUND)

        favorite_book = favorite_books.first()

        # Get the index of the favorite book
        indices = pd.Series(df_books.index, index=df_books['title']).drop_duplicates()
        if favorite_book.title not in indices:
            return Response({'status': 'Favorite book not found in precomputed data'}, status=status.HTTP_404_NOT_FOUND)

        idx = indices[favorite_book.title]
        sim_scores = list(enumerate(cosine_sim_matrix[idx]))

        # Sorting by similarity scores
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:11]  # Get top 5 recommendations

        # Getting the book titles for the recommendations
        sim_indices = [i[0] for i in sim_scores]
        recommended_books = df_books['title'].iloc[sim_indices]

        # Return the recommendations
        return Response({'recommended_titles': recommended_books.tolist()})

# JWT Auth for Registering and Login
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if username and password:
            try:
                user = User.objects.create_user(username=username, password=password)
                refresh = RefreshToken.for_user(user)  # to generate JWT tokens
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)