"""
Order serializers
"""
from rest_framework import serializers
from decimal import Decimal
from flame.models import (
    CartOrder, CartOrderItem, Address, Product, Shop,
    OrderStatusHistory
)
from ..utils import MultilingualMixin, get_language_from_request


class OrderItemSerializer(serializers.ModelSerializer, MultilingualMixin):
    """
    Order item serializer
    """
    product_title = serializers.SerializerMethodField()
    product_image = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    
    class Meta:
        model = CartOrderItem
        fields = [
            'id', 'product_title', 'product_image', 'item', 'image',
            'qty', 'price', 'total', 'price_display'
        ]
    
    def get_product_title(self, obj):
        """Get translated product title"""
        if obj.product:
            return self.get_translated_field(obj.product, 'title')
        return obj.item
    
    def get_product_image(self, obj):
        """Get product image URL"""
        if obj.product and obj.product.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.product.image.url)
            return obj.product.image.url
        elif obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f"/media/{obj.image}")
            return f"/media/{obj.image}"
        return None
    
    def get_price_display(self, obj):
        """Get formatted price based on language"""
        request = self.context.get('request')
        language_code = get_language_from_request(request) if request else 'en'
        
        from flame.models import ExchangeRate
        
        if language_code == 'my':
            rate = ExchangeRate.get_current_rate('USD', 'MMK')
            price_mmk = obj.price * rate
            total_mmk = obj.total * rate
            
            return {
                'currency': 'MMK',
                'price': f"{price_mmk:,.0f}",
                'total': f"{total_mmk:,.0f}",
                'symbol': 'Ks'
            }
        else:
            return {
                'currency': 'USD',
                'price': f"{obj.price:.2f}",
                'total': f"{obj.total:.2f}",
                'symbol': '$'
            }


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """
    Order status history serializer
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    changed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderStatusHistory
        fields = [
            'id', 'status', 'status_display', 'timestamp', 'notes',
            'location', 'carrier', 'changed_by_name'
        ]
    
    def get_changed_by_name(self, obj):
        """Get name of user who changed status"""
        if obj.changed_by:
            return f"{obj.changed_by.first_name} {obj.changed_by.last_name}".strip()
        return "System"


class OrderListSerializer(serializers.ModelSerializer, MultilingualMixin):
    """
    Order list serializer (for list views)
    """
    shop_title = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_product_status_display', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    
    class Meta:
        model = CartOrder
        fields = [
            'id', 'order_number', 'order_date', 'product_status', 'status_display',
            'progress_percentage', 'price', 'price_display', 'total_amount',
            'shop_title', 'total_items', 'tracking_number'
        ]
    
    def get_shop_title(self, obj):
        """Get translated shop title"""
        if obj.shop:
            return self.get_translated_field(obj.shop, 'title')
        return "Multiple Shops"
    
    def get_total_items(self, obj):
        """Get total number of items in order"""
        return obj.get_total_items()
    
    def get_progress_percentage(self, obj):
        """Get order progress percentage"""
        return obj.get_order_progress()
    
    def get_price_display(self, obj):
        """Get formatted price based on language"""
        request = self.context.get('request')
        language_code = get_language_from_request(request) if request else 'en'
        
        from flame.models import ExchangeRate
        
        if language_code == 'my':
            rate = ExchangeRate.get_current_rate('USD', 'MMK')
            total_mmk = obj.total_amount * rate
            
            return {
                'currency': 'MMK',
                'total': f"{total_mmk:,.0f}",
                'symbol': 'Ks'
            }
        else:
            return {
                'currency': 'USD',
                'total': f"{obj.total_amount:.2f}",
                'symbol': '$'
            }


class OrderDetailSerializer(OrderListSerializer):
    """
    Order detail serializer (for detail views)
    """
    items = OrderItemSerializer(source='cartorderitem_set', many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    delivery_info = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    can_return = serializers.SerializerMethodField()
    
    class Meta(OrderListSerializer.Meta):
        fields = OrderListSerializer.Meta.fields + [
            'items', 'status_history', 'delivery_info', 'can_cancel', 'can_return',
            'delivery_address', 'delivery_phone', 'delivery_notes',
            'estimated_delivery', 'actual_delivery', 'shipping_cost',
            'tax_amount', 'discount_amount'
        ]
    
    def get_delivery_info(self, obj):
        """Get delivery information"""
        return {
            'address': obj.delivery_address,
            'phone': obj.delivery_phone,
            'notes': obj.delivery_notes,
            'estimated_delivery': obj.estimated_delivery,
            'actual_delivery': obj.actual_delivery
        }
    
    def get_can_cancel(self, obj):
        """Check if order can be cancelled"""
        return obj.can_be_cancelled()
    
    def get_can_return(self, obj):
        """Check if order can be returned"""
        return obj.can_be_returned()


class CreateOrderSerializer(serializers.Serializer):
    """
    Serializer for creating orders
    """
    address_id = serializers.IntegerField()
    delivery_notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    payment_method = serializers.ChoiceField(
        choices=[('stripe', 'Stripe'), ('paypal', 'PayPal'), ('cod', 'Cash on Delivery')]
    )
    
    def validate_address_id(self, value):
        """Validate address belongs to user"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required")
        
        try:
            address = Address.objects.get(id=value, user=request.user)
            return value
        except Address.DoesNotExist:
            raise serializers.ValidationError("Address not found")
    
    def validate(self, attrs):
        """Validate order data"""
        request = self.context.get('request')
        
        # Check if cart has items
        cart = request.session.get('cart', {})
        if not cart:
            raise serializers.ValidationError("Cart is empty")
        
        # Validate all products in cart
        for product_id, item_data in cart.items():
            try:
                product = Product.objects.get(p_id=product_id)
                if not product.in_stock:
                    raise serializers.ValidationError(f"Product {product.title} is out of stock")
                if item_data['quantity'] > product.get_available_stock():
                    raise serializers.ValidationError(
                        f"Insufficient stock for {product.title}. Only {product.get_available_stock()} available"
                    )
            except Product.DoesNotExist:
                raise serializers.ValidationError(f"Product with ID {product_id} not found")
        
        return attrs


class UpdateOrderStatusSerializer(serializers.Serializer):
    """
    Serializer for updating order status
    """
    status = serializers.ChoiceField(choices=[
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('packed', 'Packed'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
        ('refunded', 'Refunded'),
    ])
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    tracking_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    carrier = serializers.CharField(max_length=100, required=False, allow_blank=True)


class CancelOrderSerializer(serializers.Serializer):
    """
    Serializer for cancelling orders
    """
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)