"""
Product serializers with multilingual support
"""
from rest_framework import serializers
from decimal import Decimal
from flame.models import (
    Product, ProductImages, Category, Brand, Shop, 
    ProductReview, ExchangeRate
)
from ..utils import MultilingualMixin, get_language_from_request


class CategorySerializer(serializers.ModelSerializer, MultilingualMixin):
    """
    Category serializer with translation support
    """
    title = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['c_id', 'title', 'image']
    
    def get_title(self, obj):
        return self.get_translated_field(obj, 'title')


class BrandSerializer(serializers.ModelSerializer, MultilingualMixin):
    """
    Brand serializer with translation support
    """
    title = serializers.SerializerMethodField()
    
    class Meta:
        model = Brand
        fields = ['b_id', 'title', 'brand_image']
    
    def get_title(self, obj):
        return self.get_translated_field(obj, 'title')


class ShopSerializer(serializers.ModelSerializer, MultilingualMixin):
    """
    Shop serializer with translation support
    """
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    
    class Meta:
        model = Shop
        fields = [
            'shop_id', 'title', 'description', 'image', 
            'address', 'contact', 'chat_resp_time',
            'shipping_on_time', 'authentic_rating',
            'days_return', 'warranty_period'
        ]
    
    def get_title(self, obj):
        return self.get_translated_field(obj, 'title')
    
    def get_description(self, obj):
        return self.get_translated_field(obj, 'description')


class ProductImageSerializer(serializers.ModelSerializer):
    """
    Product images serializer
    """
    class Meta:
        model = ProductImages
        fields = ['id', 'images', 'date']


class ProductReviewSerializer(serializers.ModelSerializer):
    """
    Product review serializer
    """
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductReview
        fields = [
            'id', 'user_name', 'user_full_name', 'title', 'review', 
            'rating', 'quality_rating', 'value_rating', 'delivery_rating',
            'is_verified_purchase', 'helpful_count', 'unhelpful_count',
            'date'
        ]
        read_only_fields = [
            'user_name', 'user_full_name', 'is_verified_purchase',
            'helpful_count', 'unhelpful_count', 'date'
        ]
    
    def get_user_full_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return ""


class ProductListSerializer(serializers.ModelSerializer, MultilingualMixin):
    """
    Product list serializer (for list views)
    """
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    shop = ShopSerializer(read_only=True)
    price_display = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    in_wishlist = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'p_id', 'title', 'description', 'image', 'price', 'old_price',
            'price_display', 'discount_percentage', 'category', 'brand', 'shop',
            'average_rating', 'review_count', 'in_stock', 'featured',
            'date', 'in_wishlist'
        ]
    
    def get_title(self, obj):
        return self.get_translated_field(obj, 'title')
    
    def get_description(self, obj):
        return self.get_translated_field(obj, 'description')
    
    def get_price_display(self, obj):
        """
        Get formatted price based on user's language preference
        """
        request = self.context.get('request')
        language_code = get_language_from_request(request) if request else 'en'
        
        if language_code == 'my':
            rate = ExchangeRate.get_current_rate('USD', 'MMK')
            price_mmk = obj.price * rate
            old_price_mmk = obj.old_price * rate if obj.old_price else None
            
            return {
                'currency': 'MMK',
                'price': f"{price_mmk:,.0f}",
                'old_price': f"{old_price_mmk:,.0f}" if old_price_mmk else None,
                'symbol': 'Ks'
            }
        else:
            return {
                'currency': 'USD',
                'price': f"{obj.price:.2f}",
                'old_price': f"{obj.old_price:.2f}" if obj.old_price else None,
                'symbol': '$'
            }
    
    def get_discount_percentage(self, obj):
        return obj.get_percentage() if obj.old_price and obj.old_price > obj.price else 0
    
    def get_average_rating(self, obj):
        return obj.get_average_rating()
    
    def get_review_count(self, obj):
        return obj.get_review_count()
    
    def get_in_wishlist(self, obj):
        """
        Check if product is in user's wishlist
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from flame.models import Wishlist
            return Wishlist.objects.filter(user=request.user, product=obj).exists()
        return False


class ProductDetailSerializer(ProductListSerializer):
    """
    Product detail serializer (for detail views)
    """
    specification = serializers.SerializerMethodField()
    images = ProductImageSerializer(source='productimages_set', many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    rating_breakdown = serializers.SerializerMethodField()
    similar_products = serializers.SerializerMethodField()
    frequently_bought_together = serializers.SerializerMethodField()
    stock_info = serializers.SerializerMethodField()
    
    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + [
            'specification', 'cpu', 'ram', 'sku', 'images', 'reviews',
            'rating_breakdown', 'similar_products', 'frequently_bought_together',
            'stock_info', 'digital'
        ]
    
    def get_specification(self, obj):
        return self.get_translated_field(obj, 'specification')
    
    def get_rating_breakdown(self, obj):
        return obj.get_rating_breakdown()
    
    def get_similar_products(self, obj):
        similar = obj.get_similar_products(limit=5)
        return ProductListSerializer(
            similar, many=True, context=self.context
        ).data
    
    def get_frequently_bought_together(self, obj):
        frequently_bought = obj.get_frequently_bought_together(limit=5)
        return ProductListSerializer(
            frequently_bought, many=True, context=self.context
        ).data
    
    def get_stock_info(self, obj):
        return {
            'in_stock': obj.in_stock,
            'stock_count': obj.stock_count,
            'available_stock': obj.get_available_stock(),
            'is_low_stock': obj.is_low_stock(),
            'reserved_stock': obj.reserved_stock
        }


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Product create/update serializer
    """
    class Meta:
        model = Product
        fields = [
            'title', 'description', 'specification', 'image', 'price', 'old_price',
            'category', 'brand', 'shop', 'cpu', 'ram', 'stock_count',
            'min_stock_level', 'max_stock_level', 'featured', 'digital',
            'in_stock', 'status', 'product_status'
        ]
    
    def validate_price(self, value):
        """
        Validate price is positive
        """
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value
    
    def validate(self, attrs):
        """
        Validate product data
        """
        if attrs.get('old_price') and attrs.get('price'):
            if attrs['old_price'] < attrs['price']:
                raise serializers.ValidationError(
                    "Old price cannot be less than current price"
                )
        return attrs


class ProductReviewCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating product reviews
    """
    class Meta:
        model = ProductReview
        fields = [
            'title', 'review', 'rating', 'quality_rating', 
            'value_rating', 'delivery_rating'
        ]
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
    
    def validate_quality_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Quality rating must be between 1 and 5")
        return value
    
    def validate_value_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Value rating must be between 1 and 5")
        return value
    
    def validate_delivery_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Delivery rating must be between 1 and 5")
        return value