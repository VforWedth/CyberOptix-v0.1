"""
API v1 URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from .views.auth import (
    CustomTokenObtainPairView,
    UserRegistrationView,
    UserProfileView,
    ChangePasswordView,
    PasswordResetView,
    PasswordResetConfirmView,
    user_info,
    logout_view,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# Import viewsets
from .views.product import ProductViewSet
from .views.category import CategoryViewSet, BrandViewSet
from .views.order import OrderViewSet
from .views.wishlist import WishlistViewSet
from .views.address import AddressViewSet
from .views.shop import ShopViewSet

# Import function-based views
from .views.cart import (
    get_cart, add_to_cart, update_cart_item, 
    remove_from_cart, clear_cart, cart_count
)
from .views.wishlist import (
    add_to_wishlist, remove_from_wishlist, 
    wishlist_count, clear_wishlist
)

app_name = 'v1'

# Create router for ViewSets
router = DefaultRouter()
router.register('products', ProductViewSet)
router.register('categories', CategoryViewSet)
router.register('brands', BrandViewSet)
router.register('orders', OrderViewSet)
router.register('wishlist', WishlistViewSet)
router.register('addresses', AddressViewSet)
router.register('shops', ShopViewSet)

urlpatterns = [
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:v1:schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api:v1:schema'), name='redoc'),
    
    # Authentication
    path('auth/', include([
        path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('verify/', TokenVerifyView.as_view(), name='token_verify'),
        path('register/', UserRegistrationView.as_view(), name='user_register'),
        path('logout/', logout_view, name='logout'),
        path('user/', user_info, name='user_info'),
        path('profile/', UserProfileView.as_view(), name='user_profile'),
        path('change-password/', ChangePasswordView.as_view(), name='change_password'),
        path('reset-password/', PasswordResetView.as_view(), name='password_reset'),
        path('reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    ])),
    
    # Cart endpoints
    path('cart/', include([
        path('', get_cart, name='get_cart'),
        path('add/', add_to_cart, name='add_to_cart'),
        path('update/<str:product_id>/', update_cart_item, name='update_cart_item'),
        path('remove/<str:product_id>/', remove_from_cart, name='remove_from_cart'),
        path('clear/', clear_cart, name='clear_cart'),
        path('count/', cart_count, name='cart_count'),
    ])),
    
    # Wishlist endpoints
    path('wishlist/', include([
        path('add/', add_to_wishlist, name='add_to_wishlist'),
        path('remove/<str:product_id>/', remove_from_wishlist, name='remove_from_wishlist'),
        path('count/', wishlist_count, name='wishlist_count'),
        path('clear/', clear_wishlist, name='clear_wishlist'),
    ])),
    
    # Router URLs
    path('', include(router.urls)),
]