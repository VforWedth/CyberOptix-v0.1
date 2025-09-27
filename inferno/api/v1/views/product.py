"""
Product API views
"""
from rest_framework import generics, viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count
from django.utils.translation import gettext_lazy as _

from flame.models import Product, ProductReview, Wishlist, UserBehavior
from ..serializers.product import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
    ProductReviewSerializer,
    ProductReviewCreateSerializer
)
from ..permissions import IsOwnerOrReadOnly, IsShopOwnerOrReadOnly
from ..utils import get_language_from_request
from api.common.pagination import StandardResultsSetPagination


class ProductFilter:
    """
    Custom filter for products
    """
    def filter_queryset(self, request, queryset, view):
        # Price filtering
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Category filtering
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__c_id=category)
        
        # Brand filtering
        brand = request.query_params.get('brand')
        if brand:
            queryset = queryset.filter(brand__b_id=brand)
        
        # Shop filtering
        shop = request.query_params.get('shop')
        if shop:
            queryset = queryset.filter(shop__shop_id=shop)
        
        # Stock filtering
        in_stock = request.query_params.get('in_stock')
        if in_stock:
            queryset = queryset.filter(in_stock=True)
        
        # Featured filtering
        featured = request.query_params.get('featured')
        if featured:
            queryset = queryset.filter(featured=True)
        
        # Rating filtering
        min_rating = request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.annotate(
                avg_rating=Avg('reviews__rating')
            ).filter(avg_rating__gte=min_rating)
        
        return queryset


class ProductViewSet(viewsets.ModelViewSet):
    """
    Product ViewSet with full CRUD operations
    """
    queryset = Product.objects.filter(
        product_status="published",
        status=True
    ).select_related('category', 'brand', 'shop').prefetch_related('reviews')
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'specification', 'cpu', 'ram']
    ordering_fields = ['price', 'date', 'title']
    ordering = ['-date']
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action
        """
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        else:
            return ProductDetailSerializer
    
    def get_permissions(self):
        """
        Instantiate and return the list of permissions required for this view.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsShopOwnerOrReadOnly]
        else:
            permission_classes = [IsAuthenticatedOrReadOnly]
        
        return [permission() for permission in permission_classes]
    
    def filter_queryset(self, queryset):
        """
        Apply custom filtering
        """
        queryset = super().filter_queryset(queryset)
        product_filter = ProductFilter()
        return product_filter.filter_queryset(self.request, queryset, self)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve product and track user behavior
        """
        instance = self.get_object()
        
        # Track user behavior
        if request.user.is_authenticated:
            UserBehavior.objects.create(
                user=request.user,
                product=instance,
                action='view',
                session_id=request.session.session_key,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        """
        Create product with current user as owner
        """
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticatedOrReadOnly])
    def add_to_wishlist(self, request, pk=None):
        """
        Add product to user's wishlist
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': _('Authentication required')},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        product = self.get_object()
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if created:
            # Track user behavior
            UserBehavior.objects.create(
                user=request.user,
                product=product,
                action='wishlist_add',
                session_id=request.session.session_key
            )
            
            return Response(
                {'message': _('Product added to wishlist')},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'message': _('Product already in wishlist')},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticatedOrReadOnly])
    def remove_from_wishlist(self, request, pk=None):
        """
        Remove product from user's wishlist
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': _('Authentication required')},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        product = self.get_object()
        try:
            wishlist_item = Wishlist.objects.get(
                user=request.user,
                product=product
            )
            wishlist_item.delete()
            
            # Track user behavior
            UserBehavior.objects.create(
                user=request.user,
                product=product,
                action='wishlist_remove',
                session_id=request.session.session_key
            )
            
            return Response(
                {'message': _('Product removed from wishlist')},
                status=status.HTTP_200_OK
            )
        except Wishlist.DoesNotExist:
            return Response(
                {'error': _('Product not in wishlist')},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """
        Get product reviews
        """
        product = self.get_object()
        reviews = ProductReview.objects.filter(
            product=product,
            is_approved=True
        ).select_related('user').order_by('-date')
        
        serializer = ProductReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticatedOrReadOnly])
    def add_review(self, request, pk=None):
        """
        Add review for product
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': _('Authentication required')},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        product = self.get_object()
        
        # Check if user can review this product
        if not product.can_user_review(request.user):
            return Response(
                {'error': _('You cannot review this product')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ProductReviewCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                user=request.user,
                product=product
            )
            
            # Track user behavior
            UserBehavior.objects.create(
                user=request.user,
                product=product,
                action='review',
                session_id=request.session.session_key
            )
            
            return Response(
                {'message': _('Review added successfully')},
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Get featured products
        """
        featured_products = self.get_queryset().filter(featured=True)[:10]
        serializer = ProductListSerializer(
            featured_products, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        Get popular products (most reviewed)
        """
        popular_products = self.get_queryset().annotate(
            review_count=Count('reviews')
        ).order_by('-review_count')[:10]
        
        serializer = ProductListSerializer(
            popular_products, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Advanced product search
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response([])
        
        # Build search query
        search_query = Q(title__icontains=query) | Q(description__icontains=query) | Q(specification__icontains=query)
        
        # Get language from request
        language_code = get_language_from_request(request)
        
        # Add translation fields to search for Myanmar language
        if language_code == 'my':
            search_query |= (
                Q(title_translations__my__icontains=query) |
                Q(description_translations__my__icontains=query) |
                Q(specification_translations__my__icontains=query)
            )
        
        # Apply search
        products = self.get_queryset().filter(search_query)
        
        # Track search behavior
        if request.user.is_authenticated:
            UserBehavior.objects.create(
                user=request.user,
                action='search',
                search_query=query,
                session_id=request.session.session_key
            )
        
        # Apply additional filters
        products = self.filter_queryset(products)
        
        # Paginate results
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(
            products, many=True, context={'request': request}
        )
        return Response(serializer.data)