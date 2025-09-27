"""
Category and Brand API views
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count

from flame.models import Category, Brand, Product
from ..serializers.category import (
    CategoryListSerializer,
    CategoryDetailSerializer,
    CategoryWithProductsSerializer,
    BrandListSerializer,
    BrandDetailSerializer,
    BrandWithProductsSerializer
)
from ..serializers.product import ProductListSerializer
from api.common.pagination import StandardResultsSetPagination


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Category ViewSet - Read only
    """
    queryset = Category.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering = ['title']
    lookup_field = 'c_id'
    lookup_url_kwarg = 'c_id'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return CategoryListSerializer
        elif self.action == 'products':
            return CategoryWithProductsSerializer
        else:
            return CategoryDetailSerializer
    
    def get_queryset(self):
        """Get categories with product counts"""
        return Category.objects.annotate(
            product_count=Count('category')
        ).order_by('title')
    
    @action(detail=True, methods=['get'])
    def products(self, request, c_id=None):
        """
        Get products in a specific category
        """
        category = self.get_object()
        
        # Get products in this category
        products = Product.objects.filter(
            category=category,
            product_status="published",
            status=True
        ).select_related('shop', 'brand').prefetch_related('reviews')
        
        # Apply filters
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        brand = request.query_params.get('brand')
        shop = request.query_params.get('shop')
        in_stock = request.query_params.get('in_stock')
        
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
        if brand:
            products = products.filter(brand__b_id=brand)
        if shop:
            products = products.filter(shop__shop_id=shop)
        if in_stock:
            products = products.filter(in_stock=True)
        
        # Apply ordering
        ordering = request.query_params.get('ordering', '-date')
        if ordering in ['price', '-price', 'title', '-title', 'date', '-date']:
            products = products.order_by(ordering)
        else:
            products = products.order_by('-date')
        
        # Paginate
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
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        Get most popular categories (by product count)
        """
        categories = self.get_queryset().filter(
            category__product_status="published",
            category__status=True
        ).annotate(
            active_product_count=Count('category', distinct=True)
        ).filter(active_product_count__gt=0).order_by('-active_product_count')[:10]
        
        serializer = CategoryListSerializer(
            categories, many=True, context={'request': request}
        )
        return Response(serializer.data)


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Brand ViewSet - Read only
    """
    queryset = Brand.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering = ['title']
    lookup_field = 'b_id'
    lookup_url_kwarg = 'b_id'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return BrandListSerializer
        elif self.action == 'products':
            return BrandWithProductsSerializer
        else:
            return BrandDetailSerializer
    
    def get_queryset(self):
        """Get brands with product counts"""
        return Brand.objects.annotate(
            product_count=Count('brand_products')
        ).order_by('title')
    
    @action(detail=True, methods=['get'])
    def products(self, request, b_id=None):
        """
        Get products for a specific brand
        """
        brand = self.get_object()
        
        # Get products for this brand
        products = Product.objects.filter(
            brand=brand,
            product_status="published",
            status=True
        ).select_related('shop', 'category').prefetch_related('reviews')
        
        # Apply filters
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        category = request.query_params.get('category')
        shop = request.query_params.get('shop')
        in_stock = request.query_params.get('in_stock')
        
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
        if category:
            products = products.filter(category__c_id=category)
        if shop:
            products = products.filter(shop__shop_id=shop)
        if in_stock:
            products = products.filter(in_stock=True)
        
        # Apply ordering
        ordering = request.query_params.get('ordering', '-date')
        if ordering in ['price', '-price', 'title', '-title', 'date', '-date']:
            products = products.order_by(ordering)
        else:
            products = products.order_by('-date')
        
        # Paginate
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
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        Get most popular brands (by product count)
        """
        brands = self.get_queryset().filter(
            brand_products__product_status="published",
            brand_products__status=True
        ).annotate(
            active_product_count=Count('brand_products', distinct=True)
        ).filter(active_product_count__gt=0).order_by('-active_product_count')[:10]
        
        serializer = BrandListSerializer(
            brands, many=True, context={'request': request}
        )
        return Response(serializer.data)