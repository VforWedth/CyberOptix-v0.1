"""
Wishlist API views
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from flame.models import Wishlist, Product, UserBehavior
from ..serializers.wishlist import WishlistItemSerializer, AddToWishlistSerializer
from api.common.pagination import StandardResultsSetPagination


class WishlistViewSet(viewsets.ModelViewSet):
    """
    Wishlist ViewSet for managing user wishlist
    """
    queryset = Wishlist.objects.all()
    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Get wishlist items for current user"""
        return Wishlist.objects.filter(
            user=self.request.user
        ).select_related('product__shop', 'product__category', 'product__brand').order_by('-date')
    
    def create(self, request, *args, **kwargs):
        """Add item to wishlist"""
        serializer = AddToWishlistSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = serializer.validated_data['product_id']
        
        try:
            product = Product.objects.get(p_id=product_id)
            
            # Create wishlist item
            wishlist_item = Wishlist.objects.create(
                user=request.user,
                product=product
            )
            
            # Track user behavior
            UserBehavior.objects.create(
                user=request.user,
                product=product,
                action='wishlist_add',
                session_id=request.session.session_key
            )
            
            # Return the created item
            response_serializer = WishlistItemSerializer(
                wishlist_item, context={'request': request}
            )
            
            return Response({
                'message': _('Product added to wishlist successfully'),
                'item': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Product.DoesNotExist:
            return Response({
                'error': _('Product not found')
            }, status=status.HTTP_404_NOT_FOUND)
    
    def destroy(self, request, *args, **kwargs):
        """Remove item from wishlist"""
        instance = self.get_object()
        product = instance.product
        
        # Track user behavior
        UserBehavior.objects.create(
            user=request.user,
            product=product,
            action='wishlist_remove',
            session_id=request.session.session_key
        )
        
        self.perform_destroy(instance)
        
        return Response({
            'message': _('Product removed from wishlist successfully')
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_to_wishlist(request):
    """
    Add product to wishlist (alternative endpoint)
    """
    serializer = AddToWishlistSerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    product_id = serializer.validated_data['product_id']
    
    try:
        product = Product.objects.get(p_id=product_id)
        
        # Create wishlist item
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
            
            return Response({
                'message': _('Product added to wishlist successfully')
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'message': _('Product already in wishlist')
            }, status=status.HTTP_200_OK)
            
    except Product.DoesNotExist:
        return Response({
            'error': _('Product not found')
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_from_wishlist(request, product_id):
    """
    Remove product from wishlist by product ID
    """
    try:
        product = Product.objects.get(p_id=product_id)
        wishlist_item = Wishlist.objects.get(
            user=request.user,
            product=product
        )
        
        # Track user behavior
        UserBehavior.objects.create(
            user=request.user,
            product=product,
            action='wishlist_remove',
            session_id=request.session.session_key
        )
        
        wishlist_item.delete()
        
        return Response({
            'message': _('Product removed from wishlist successfully')
        }, status=status.HTTP_200_OK)
        
    except Product.DoesNotExist:
        return Response({
            'error': _('Product not found')
        }, status=status.HTTP_404_NOT_FOUND)
    except Wishlist.DoesNotExist:
        return Response({
            'error': _('Product not in wishlist')
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def wishlist_count(request):
    """
    Get total items count in wishlist
    """
    count = Wishlist.objects.filter(user=request.user).count()
    
    return Response({
        'count': count
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def clear_wishlist(request):
    """
    Clear entire wishlist
    """
    deleted_count = Wishlist.objects.filter(user=request.user).delete()[0]
    
    return Response({
        'message': _('Wishlist cleared successfully'),
        'removed_items': deleted_count
    }, status=status.HTTP_200_OK)