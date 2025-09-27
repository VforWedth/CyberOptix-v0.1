"""
Shop API views
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from flame.models import Shop, Product
from ..serializers.shop import (
    ShopListSerializer,
    ShopDetailSerializer,
    CreateShopSerializer,
    UpdateShopSerializer
)
from ..serializers.product import ProductListSerializer
from api.common.pagination import StandardResultsSetPagination


class ShopViewSet(viewsets.ModelViewSet):
    """
    Shop ViewSet for managing shops
    """
    queryset = Shop.objects.all()
    pagination_class = StandardResultsSetPagination
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        else:
            return [permissions.AllowAny()]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return CreateShopSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateShopSerializer
        elif self.action == 'retrieve':
            return ShopDetailSerializer
        else:
            return ShopListSerializer
    
    def get_queryset(self):
        """Get shops queryset with optimized queries"""
        return Shop.objects.select_related('user').prefetch_related('products').order_by('-id')
    
    def perform_create(self, serializer):
        """Create shop with current user as owner"""
        # Generate slug from title
        title = serializer.validated_data.get('title', '')
        slug = slugify(title)
        
        # Ensure unique slug
        counter = 1
        original_slug = slug
        while Shop.objects.filter(slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        shop = serializer.save(user=self.request.user, slug=slug)
        return shop
    
    def create(self, request, *args, **kwargs):
        """Create new shop"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        shop = self.perform_create(serializer)
        
        response_serializer = ShopDetailSerializer(shop, context={'request': request})
        
        return Response({
            'message': _('Shop created successfully'),
            'shop': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update shop"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check if user owns the shop
        if instance.user != request.user:
            return Response({
                'error': _('You can only update your own shops')
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Update slug if title changed
        if 'title' in serializer.validated_data:
            title = serializer.validated_data['title']
            slug = slugify(title)
            
            # Ensure unique slug (excluding current shop)
            counter = 1
            original_slug = slug
            while Shop.objects.filter(slug=slug).exclude(id=instance.id).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            serializer.validated_data['slug'] = slug
        
        shop = serializer.save()
        
        response_serializer = ShopDetailSerializer(shop, context={'request': request})
        
        return Response({
            'message': _('Shop updated successfully'),
            'shop': response_serializer.data
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        """Delete shop"""
        instance = self.get_object()
        
        # Check if user owns the shop
        if instance.user != request.user:
            return Response({
                'error': _('You can only delete your own shops')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if shop has products
        if instance.products.filter(status=True).exists():
            return Response({
                'error': _('Cannot delete shop with active products. Please remove or deactivate products first.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_destroy(instance)
        
        return Response({
            'message': _('Shop deleted successfully')
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get all products from a specific shop"""
        shop = self.get_object()
        
        products = Product.objects.filter(
            shop=shop,
            product_status='published',
            status=True
        ).select_related('shop', 'category', 'brand').order_by('-date')
        
        # Apply pagination
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_shops(self, request):
        """Get current user's shops"""
        shops = self.get_queryset().filter(user=request.user)
        
        # Apply pagination
        page = self.paginate_queryset(shops)
        if page is not None:
            serializer = ShopListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ShopListSerializer(shops, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get shop statistics"""
        shop = self.get_object()
        
        # Get shop products
        products = shop.products.filter(
            product_status='published',
            status=True
        )
        
        # Calculate statistics
        total_products = products.count()
        total_orders = 0
        total_revenue = 0
        total_reviews = 0
        
        # Calculate orders and revenue from OrderItem
        for product in products:
            order_items = product.orderitems.select_related('order')
            total_orders += order_items.count()
            total_revenue += sum([item.price * item.qty for item in order_items])
            total_reviews += product.reviews.count()
        
        # Calculate average rating
        average_rating = 0
        if total_reviews > 0:
            total_rating_sum = sum([
                sum([review.rating for review in product.reviews.all()])
                for product in products
            ])
            average_rating = round(total_rating_sum / total_reviews, 2)
        
        return Response({
            'shop_id': shop.shop_id,
            'shop_name': shop.get_translated_title(request.LANGUAGE_CODE),
            'total_products': total_products,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'total_reviews': total_reviews,
            'average_rating': average_rating,
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Get shop by shop_id or slug"""
        # Try to get by shop_id first, then by slug
        lookup_value = kwargs.get('pk')
        
        try:
            if lookup_value.startswith('shop'):
                # It's a shop_id
                instance = get_object_or_404(Shop, shop_id=lookup_value)
            else:
                # It's a slug
                instance = get_object_or_404(Shop, slug=lookup_value)
        except:
            instance = self.get_object()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)