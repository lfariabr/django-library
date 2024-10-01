from rest_framework.routers import DefaultRouter
from .views import BookViewSet, AuthorViewSet, UserFavoritesViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'books', BookViewSet)  # to handle all /books/ routes
router.register(r'authors', AuthorViewSet)  # to handle all /authors/ routes
router.register(r'user_favorites', UserFavoritesViewSet, basename='user_favorites')  # to handle /user_favorites/ routes

# URLs for books app
urlpatterns = [
    path('', include(router.urls)),  # Include all the routes from the router
]