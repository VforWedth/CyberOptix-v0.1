"""
Cart serializers
"""
from rest_framework import serializers
from decimal import Decimal
from flame.models import Product, Shop
from ..utils import MultilingualMixin, get_language_from_request


class CartItemSerializer(serializers.Serializer):
    """
    Cart item serializer for session-based cart
    """
    product_id = serializers.CharField()
    shop_id = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    # Product details
    product_title = serializers.SerializerMethodField()
    product_image = serializers.SerializerMethodField()
    shop_title = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()
    available_stock = serializers.SerializerMethodField()
    
    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        self.shop = kwargs.pop('shop', None)
        super().__init__(*args, **kwargs)
    
    def get_product_title(self, obj):
        """Get translated product title"""
        if self.product:
            request = self.context.get('request')
            language_code = get_language_from_request(request) if request else 'en'
            return self.product.get_translated_title(language_code)
        return ""
    
    def get_product_image(self, obj):
        """Get product image URL"""
        if self.product and self.product.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(self.product.image.url)
            return self.product.image.url
        return None
    
    def get_shop_title(self, obj):
        """Get translated shop title"""
        if self.shop:
            request = self.context.get('request')
            language_code = get_language_from_request(request) if request else 'en'
            return self.shop.get_translated_title(language_code)
        return ""
    
    def get_price_display(self, obj):
        """Get formatted price based on language"""
        if not self.product:
            return {}
        
        request = self.context.get('request')
        language_code = get_language_from_request(request) if request else 'en'
        
        from flame.models import ExchangeRate
        
        if language_code == 'my':
            rate = ExchangeRate.get_current_rate('USD', 'MMK')
            price_mmk = self.product.price * rate
            total_mmk = price_mmk * obj.get('quantity', 1)
            
            return {
                'currency': 'MMK',
                'price': f"{price_mmk:,.0f}",
                'total': f"{total_mmk:,.0f}",
                'symbol': 'Ks'
            }
        else:
            price_usd = self.product.price
            total_usd = price_usd * obj.get('quantity', 1)
            
            return {
                'currency': 'USD',
                'price': f"{price_usd:.2f}",
                'total': f"{total_usd:.2f}",
                'symbol': '$'
            }
    
    def get_in_stock(self, obj):
        """Check if product is in stock"""
        return self.product.in_stock if self.product else False
    
    def get_available_stock(self, obj):
        """Get available stock quantity"""
        return self.product.get_available_stock() if self.product else 0


class CartSerializer(serializers.Serializer):
    """
    Complete cart serializer
    """
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_price_display = serializers.SerializerMethodField()
    shops = serializers.SerializerMethodField()
    
    def get_total_price_display(self, obj):
        """Get formatted total price"""
        request = self.context.get('request')
        language_code = get_language_from_request(request) if request else 'en'
        total_price = obj.get('total_price', Decimal('0'))
        
        from flame.models import ExchangeRate
        
        if language_code == 'my':
            rate = ExchangeRate.get_current_rate('USD', 'MMK')
            total_mmk = total_price * rate
            return {
                'currency': 'MMK',
                'total': f"{total_mmk:,.0f}",
                'symbol': 'Ks'
            }
        else:
            return {
                'currency': 'USD',
                'total': f"{total_price:.2f}",
                'symbol': '$'
            }
    
    def get_shops(self, obj):
        """Get list of shops in cart with their totals"""
        shops_data = {}
        items = obj.get('items', [])
        
        for item_data in items:
            shop_id = item_data.get('shop_id')
            if shop_id not in shops_data:
                try:
                    shop = Shop.objects.get(shop_id=shop_id)
                    request = self.context.get('request')
                    language_code = get_language_from_request(request) if request else 'en'
                    
                    shops_data[shop_id] = {
                        'shop_id': shop_id,
                        'title': shop.get_translated_title(language_code),
                        'items_count': 0,
                        'total_price': Decimal('0')
                    }
                except Shop.DoesNotExist:
                    continue
            
            shops_data[shop_id]['items_count'] += 1
            shops_data[shop_id]['total_price'] += item_data.get('total', Decimal('0'))
        
        return list(shops_data.values())


class AddToCartSerializer(serializers.Serializer):
    """
    Serializer for adding items to cart
    """
    product_id = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    
    def validate_product_id(self, value):
        """Validate product exists and is available"""
        try:
            product = Product.objects.get(p_id=value, product_status="published", status=True)
            if not product.in_stock:
                raise serializers.ValidationError("Product is out of stock")
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")
    
    def validate(self, attrs):
        """Validate quantity against available stock"""
        try:
            product = Product.objects.get(p_id=attrs['product_id'])
            if attrs['quantity'] > product.get_available_stock():
                raise serializers.ValidationError(
                    f"Only {product.get_available_stock()} items available in stock"
                )
        except Product.DoesNotExist:
            pass  # Already handled in validate_product_id
        
        return attrs


class UpdateCartItemSerializer(serializers.Serializer):
    """
    Serializer for updating cart item quantity
    """
    quantity = serializers.IntegerField(min_value=0)
    
    def validate_quantity(self, value):
        """Validate quantity (0 means remove item)"""
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative")
        return value