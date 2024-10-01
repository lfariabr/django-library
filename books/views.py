from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from .models import Book, Author, UserFavorites
from .serializers import BookSerializer, AuthorSerializer, UserFavoritesSerializer
from rest_framework.decorators import action, api_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination

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
        return UserFavorites.objects.filter(user=self.request.user).order_by('id')
    
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
        # Recebendo a lista de IDs de livros
        book_ids = request.data.get('book_ids', [])

        # Verificação para garantir que IDs foram fornecidos
        if not book_ids:
            return Response({'status': 'No books provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Garantindo que só haja um registro de favoritos por usuário
        user_favorites, _ = UserFavorites.objects.get_or_create(user=request.user)

        # Filtrando os livros com os IDs fornecidos
        books = Book.objects.filter(id__in=book_ids)

        # Verificando se os livros foram encontrados no banco de dados
        if not books.exists():
            return Response({'status': 'No books found with the provided IDs'}, status=status.HTTP_400_BAD_REQUEST)

        # Verificando se a adição de novos livros excede o limite
        if user_favorites.favorites.count() + books.count() > 10:
            return Response({'status': 'Maximum number of books reached'}, status=status.HTTP_400_BAD_REQUEST)

        # Adicionando livros aos favoritos
        user_favorites.favorites.add(*books)

        # Retornando a resposta com a lista atualizada de favoritos
        return Response({
            'status': f'{books.count()} books added to favorites!',
            'favorites': [book.title for book in user_favorites.favorites.all()]
        }, status=status.HTTP_201_CREATED)
        

    # Removing Favorites
    @action(detail=False, methods=['POST'])
    def remove_favorite(self, request):
        book_id = request.data.get('book_id')

        # Garantir que o ID do livro foi fornecido
        if not book_id:
            return Response({'status': 'No book ID provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Buscar o livro pelo ID
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({'status': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

        # Buscar ou criar favoritos do usuário
        user_favorites, _ = UserFavorites.objects.get_or_create(user=request.user)

        # Remover o livro dos favoritos
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
    @action(detail=False, methods=['GET'])
    def recommendations(self, request):
        
        # Getting user favorites
        user_favorites, _ = UserFavorites.objects.get_or_create(user=request.user)
        favorite_books = user_favorites.favorites.all()

        print("Favorites: ", favorite_books)

        # Getting a list of authors of the user's favorite books
        favorite_authors = set(book.author for book in favorite_books)
        # Recommend books bys these authors... that were not added to favorites yet
        recommended_books = Book.objects.filter(author__in=favorite_authors).exclude(id__in=favorite_books.values_list('id', flat=True))[:5]
        print("Recommended: ", recommended_books)

        if not recommended_books.exists():
            return Response({'status': 'No recommendations found'}, status=status.HTTP_404_NOT_FOUND)
        # Serializing the recommended books
        serializer = BookSerializer(recommended_books, many=True)
        return Response(serializer.data)

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