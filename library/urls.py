from django.contrib import admin
from django.urls import path, include
from books.views import register  # Import the register view from the main views.py
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.conf.urls.static import static


schema_view = get_schema_view(
   openapi.Info(
      title="Library API Django Project",
      default_version='v1',
      description="Library API",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="lfariabr@gmail.com"),
      license=openapi.License(name="Luis Faria"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin URL
    path('api/', include('books.urls')),  # Include all API URLs from books/urls.py
    path('api/register/', register, name='register'),  # User registration
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # JWT login
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # JWT token refresh
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

