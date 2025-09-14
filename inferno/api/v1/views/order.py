"""
Order API views
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import uuid

from flame.models import (
    CartOrder, CartOrderItem, Address, Product, Shop,
    OrderStatusHistory, UserBehavior
)
from ..serializers.order import (
    OrderListSerializer,
    OrderDetailSerializer,
    CreateOrderSerializer,
    UpdateOrderStatusSerializer,
    CancelOrderSerializer
)
from ..permissions import IsOwnerOrReadOnly, IsSuperUserOrShopOwner
from api.common.pagination import StandardResultsSetPagination


class OrderViewSet(viewsets.ModelViewSet):
    """
    Order ViewSet for managing orders
    """
    queryset = CartOrder.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    lookup_field = 'order_number'
    lookup_url_kwarg = 'order_number'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'create':
            return CreateOrderSerializer
        elif self.action == 'update_status':
            return UpdateOrderStatusSerializer
        elif self.action == 'cancel':
            return CancelOrderSerializer
        else:
            return OrderDetailSerializer
    
    def get_queryset(self):
        """Get orders for current user or all orders for admin"""
        user = self.request.user
        
        if user.is_superuser:
            # Admin can see all orders
            return CartOrder.objects.all().select_related(
                'user', 'shop'
            ).prefetch_related(
                'cartorderitem_set__product',
                'status_history'
            ).order_by('-order_date')
        else:
            # Regular users see only their orders
            return CartOrder.objects.filter(user=user).select_related(
                'shop'
            ).prefetch_related(
                'cartorderitem_set__product',
                'status_history'
            ).order_by('-order_date')
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['update_status']:
            permission_classes = [IsSuperUserOrShopOwner]
        elif self.action in ['cancel']:
            permission_classes = [IsOwnerOrReadOnly]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create new order from cart
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get validated data
        address_id = serializer.validated_data['address_id']
        delivery_notes = serializer.validated_data.get('delivery_notes', '')
        payment_method = serializer.validated_data['payment_method']
        
        # Get cart from session
        cart = request.session.get('cart', {})
        if not cart:
            return Response({
                'error': _('Cart is empty')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get delivery address
        try:
            address = Address.objects.get(id=address_id, user=request.user)
        except Address.DoesNotExist:
            return Response({
                'error': _('Address not found')
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Group cart items by shop
        shops_orders = {}
        total_order_amount = Decimal('0')
        
        for product_id, item_data in cart.items():
            try:
                product = Product.objects.select_for_update().get(p_id=product_id)
                quantity = item_data['quantity']
                
                # Check stock availability
                if not product.can_fulfill_order(quantity):
                    return Response({
                        'error': _('Insufficient stock for {}. Only {} available').format(
                            product.title, product.get_available_stock()
                        )
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Reserve stock
                product.reserve_stock(quantity)
                
                shop_id = product.shop.shop_id if product.shop else 'no_shop'
                
                if shop_id not in shops_orders:
                    shops_orders[shop_id] = {
                        'shop': product.shop,
                        'items': [],
                        'total': Decimal('0')
                    }
                
                item_total = product.price * quantity
                shops_orders[shop_id]['items'].append({
                    'product': product,
                    'quantity': quantity,
                    'price': product.price,
                    'total': item_total
                })
                shops_orders[shop_id]['total'] += item_total
                total_order_amount += item_total
                
            except Product.DoesNotExist:
                return Response({
                    'error': _('Product with ID {} not found').format(product_id)
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Create orders for each shop
        created_orders = []
        
        for shop_id, shop_data in shops_orders.items():
            # Create order
            order = CartOrder.objects.create(
                user=request.user,
                shop=shop_data['shop'],
                price=shop_data['total'],  # Legacy field
                total_amount=shop_data['total'],
                delivery_address=address.address,
                delivery_phone=address.mobile,
                delivery_notes=delivery_notes,
                product_status='pending'
            )
            
            # Create order items
            for item in shop_data['items']:
                CartOrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    invoice_no=order.order_number,
                    product_status='pending',
                    item=item['product'].title,
                    image=item['product'].image.name if item['product'].image else '',
                    qty=item['quantity'],
                    price=item['price'],
                    total=item['total']
                )
                
                # Track user behavior
                UserBehavior.objects.create(
                    user=request.user,
                    product=item['product'],
                    action='purchase',
                    session_id=request.session.session_key
                )
            
            # Create initial status history
            OrderStatusHistory.objects.create(
                order=order,
                status='pending',
                changed_by=request.user,
                notes='Order placed'
            )
            
            created_orders.append(order)
        
        # Clear cart
        request.session['cart'] = {}
        request.session.modified = True
        
        # Return created orders
        serializer = OrderDetailSerializer(
            created_orders, many=True, context={'request': request}
        )
        
        return Response({
            'message': _('Order(s) created successfully'),
            'orders': serializer.data,
            'total_orders': len(created_orders),
            'payment_method': payment_method
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, order_number=None):
        """
        Update order status (admin/shop owners only)
        """
        order = self.get_object()
        serializer = UpdateOrderStatusSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')
        tracking_number = serializer.validated_data.get('tracking_number', '')
        location = serializer.validated_data.get('location', '')
        carrier = serializer.validated_data.get('carrier', '')
        
        # Update order
        old_status = order.product_status
        order.product_status = new_status
        
        # Update status timestamps
        if new_status == 'confirmed':
            order.confirmed_at = timezone.now()
        elif new_status == 'processing':
            order.processed_at = timezone.now()
        elif new_status == 'packed':
            order.packed_at = timezone.now()
        elif new_status == 'shipped':
            order.shipped_at = timezone.now()
            if tracking_number:
                order.tracking_number = tracking_number
        elif new_status == 'delivered':
            order.delivered_at = timezone.now()
            order.actual_delivery = timezone.now()
            
            # Fulfill the order (reduce actual stock)
            for item in order.cartorderitem_set.all():
                if item.product:
                    item.product.fulfill_order(item.qty)
        
        order.save()
        
        # Create status history entry
        OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            changed_by=request.user,
            notes=notes,
            location=location,
            carrier=carrier
        )
        
        serializer = OrderDetailSerializer(order, context={'request': request})
        
        return Response({
            'message': _('Order status updated successfully'),
            'order': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, order_number=None):
        """
        Cancel order (user or admin)
        """
        order = self.get_object()
        
        if not order.can_be_cancelled():
            return Response({
                'error': _('Order cannot be cancelled at this stage')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = CancelOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        reason = serializer.validated_data.get('reason', 'Cancelled by user')
        
        # Update order status
        order.product_status = 'cancelled'
        order.save()
        
        # Release reserved stock
        for item in order.cartorderitem_set.all():
            if item.product:
                item.product.release_reserved_stock(item.qty)
        
        # Create status history entry
        OrderStatusHistory.objects.create(
            order=order,
            status='cancelled',
            changed_by=request.user,
            notes=reason
        )
        
        return Response({
            'message': _('Order cancelled successfully'),
            'order_number': order.order_number
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def track(self, request, order_number=None):
        """
        Get order tracking information
        """
        order = self.get_object()
        
        tracking_info = {
            'order_number': order.order_number,
            'current_status': order.product_status,
            'current_status_display': order.get_product_status_display(),
            'progress_percentage': order.get_order_progress(),
            'tracking_number': order.tracking_number,
            'estimated_delivery': order.estimated_delivery,
            'actual_delivery': order.actual_delivery,
            'status_history': []
        }
        
        # Add status history
        for history in order.status_history.order_by('timestamp'):
            tracking_info['status_history'].append({
                'status': history.status,
                'status_display': history.get_status_display(),
                'timestamp': history.timestamp,
                'notes': history.notes,
                'location': history.location,
                'carrier': history.carrier
            })
        
        return Response(tracking_info, status=status.HTTP_200_OK)