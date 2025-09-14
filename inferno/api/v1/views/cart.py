"""
Cart API views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

from flame.models import Product, Shop, UserBehavior
from ..serializers.cart import (
    CartSerializer,
    CartItemSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer
)


def get_cart_from_session(request):
    """
    Get cart data from session
    """
    cart = request.session.get('cart', {})
    return cart


def save_cart_to_session(request, cart):
    """
    Save cart data to session
    """
    request.session['cart'] = cart
    request.session.modified = True


def calculate_cart_totals(cart_items):
    """
    Calculate cart totals
    """
    total_items = 0
    total_price = Decimal('0')
    
    for item in cart_items:
        total_items += item['quantity']
        total_price += item['total']
    
    return total_items, total_price


def serialize_cart_items(cart_data, request):
    """
    Convert cart data to serialized format with product details
    """
    items = []
    
    for product_id, item_data in cart_data.items():
        try:
            product = Product.objects.get(p_id=product_id)
            shop = product.shop
            
            item_serialized = {
                'product_id': product_id,
                'shop_id': shop.shop_id if shop else '',
                'quantity': item_data['quantity'],
                'price': product.price,
                'total': product.price * item_data['quantity']
            }
            
            # Use serializer to get formatted data
            serializer = CartItemSerializer(
                item_serialized, 
                context={'request': request},
                product=product,
                shop=shop
            )
            items.append(serializer.data)
            
        except Product.DoesNotExist:
            # Remove invalid items from cart
            continue
    
    return items


@api_view(['GET'])
def get_cart(request):
    """
    Get cart contents
    """
    cart_data = get_cart_from_session(request)
    items = serialize_cart_items(cart_data, request)
    
    total_items, total_price = calculate_cart_totals(items)
    
    cart_summary = {
        'items': items,
        'total_items': total_items,
        'total_price': total_price
    }
    
    serializer = CartSerializer(cart_summary, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
def add_to_cart(request):
    """
    Add item to cart
    """
    serializer = AddToCartSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    product_id = serializer.validated_data['product_id']
    quantity = serializer.validated_data['quantity']
    
    try:
        product = Product.objects.get(p_id=product_id)
        
        # Get current cart
        cart = get_cart_from_session(request)
        
        # Check if item already in cart
        if product_id in cart:
            new_quantity = cart[product_id]['quantity'] + quantity
            
            # Check stock availability
            if new_quantity > product.get_available_stock():
                return Response({
                    'error': _('Insufficient stock. Only {} items available').format(
                        product.get_available_stock()
                    )
                }, status=status.HTTP_400_BAD_REQUEST)
            
            cart[product_id]['quantity'] = new_quantity
        else:
            # Add new item
            cart[product_id] = {
                'quantity': quantity,
                'added_at': str(__import__('datetime').datetime.now())
            }
        
        # Save cart to session
        save_cart_to_session(request, cart)
        
        # Track user behavior
        if request.user.is_authenticated:
            UserBehavior.objects.create(
                user=request.user,
                product=product,
                action='cart_add',
                session_id=request.session.session_key
            )
        
        # Return updated cart
        items = serialize_cart_items(cart, request)
        total_items, total_price = calculate_cart_totals(items)
        
        cart_summary = {
            'items': items,
            'total_items': total_items,
            'total_price': total_price
        }
        
        serializer = CartSerializer(cart_summary, context={'request': request})
        
        return Response({
            'message': _('Item added to cart successfully'),
            'cart': serializer.data
        }, status=status.HTTP_201_CREATED)
        
    except Product.DoesNotExist:
        return Response({
            'error': _('Product not found')
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
def update_cart_item(request, product_id):
    """
    Update cart item quantity
    """
    serializer = UpdateCartItemSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    quantity = serializer.validated_data['quantity']
    
    try:
        product = Product.objects.get(p_id=product_id)
        cart = get_cart_from_session(request)
        
        if product_id not in cart:
            return Response({
                'error': _('Item not found in cart')
            }, status=status.HTTP_404_NOT_FOUND)
        
        if quantity == 0:
            # Remove item from cart
            del cart[product_id]
            
            # Track user behavior
            if request.user.is_authenticated:
                UserBehavior.objects.create(
                    user=request.user,
                    product=product,
                    action='cart_remove',
                    session_id=request.session.session_key
                )
            
            message = _('Item removed from cart')
        else:
            # Check stock availability
            if quantity > product.get_available_stock():
                return Response({
                    'error': _('Insufficient stock. Only {} items available').format(
                        product.get_available_stock()
                    )
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update quantity
            cart[product_id]['quantity'] = quantity
            message = _('Cart item updated successfully')
        
        # Save cart to session
        save_cart_to_session(request, cart)
        
        # Return updated cart
        items = serialize_cart_items(cart, request)
        total_items, total_price = calculate_cart_totals(items)
        
        cart_summary = {
            'items': items,
            'total_items': total_items,
            'total_price': total_price
        }
        
        serializer = CartSerializer(cart_summary, context={'request': request})
        
        return Response({
            'message': message,
            'cart': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Product.DoesNotExist:
        return Response({
            'error': _('Product not found')
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
def remove_from_cart(request, product_id):
    """
    Remove item from cart
    """
    try:
        product = Product.objects.get(p_id=product_id)
        cart = get_cart_from_session(request)
        
        if product_id not in cart:
            return Response({
                'error': _('Item not found in cart')
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Remove item
        del cart[product_id]
        save_cart_to_session(request, cart)
        
        # Track user behavior
        if request.user.is_authenticated:
            UserBehavior.objects.create(
                user=request.user,
                product=product,
                action='cart_remove',
                session_id=request.session.session_key
            )
        
        # Return updated cart
        items = serialize_cart_items(cart, request)
        total_items, total_price = calculate_cart_totals(items)
        
        cart_summary = {
            'items': items,
            'total_items': total_items,
            'total_price': total_price
        }
        
        serializer = CartSerializer(cart_summary, context={'request': request})
        
        return Response({
            'message': _('Item removed from cart successfully'),
            'cart': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Product.DoesNotExist:
        return Response({
            'error': _('Product not found')
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
def clear_cart(request):
    """
    Clear entire cart
    """
    # Clear cart from session
    request.session['cart'] = {}
    request.session.modified = True
    
    return Response({
        'message': _('Cart cleared successfully'),
        'cart': {
            'items': [],
            'total_items': 0,
            'total_price': '0.00'
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def cart_count(request):
    """
    Get total items count in cart
    """
    cart = get_cart_from_session(request)
    total_items = sum(item['quantity'] for item in cart.values())
    
    return Response({
        'count': total_items
    }, status=status.HTTP_200_OK)