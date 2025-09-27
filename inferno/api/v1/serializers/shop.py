"""
Shop serializers
"""
from rest_framework import serializers
from django.utils.translation import get_language
from flame.models import Shop, Product


class ShopListSerializer(serializers.ModelSerializer):
    """
    Shop list serializer with basic info
    """
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Shop
        fields = [
            'shop_id', 'slug', 'title', 'description', 'image',
            'address', 'contact', 'product_count', 'average_rating'
        ]
    
    def get_title(self, obj):
        """Get translated title based on current language"""
        language_code = get_language()
        return obj.get_translated_title(language_code)
    
    def get_description(self, obj):
        """Get translated description based on current language"""
        language_code = get_language()
        return obj.get_translated_description(language_code)
    
    def get_product_count(self, obj):
        """Get total number of active products in shop"""
        return obj.products.filter(
            product_status='published',
            status=True
        ).count()
    
    def get_average_rating(self, obj):
        """Calculate average rating from all shop products"""
        products = obj.products.filter(
            product_status='published',
            status=True
        ).prefetch_related('reviews')
        
        total_ratings = 0
        total_reviews = 0
        
        for product in products:
            product_reviews = product.reviews.all()
            if product_reviews:
                total_ratings += sum([review.rating for review in product_reviews])
                total_reviews += len(product_reviews)
        
        if total_reviews == 0:
            return 0
        
        return round(total_ratings / total_reviews, 2)


class ShopDetailSerializer(serializers.ModelSerializer):
    """
    Shop detail serializer with complete information
    """
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    recent_products = serializers.SerializerMethodField()
    
    class Meta:
        model = Shop
        fields = [
            'shop_id', 'slug', 'title', 'description', 'image',
            'address', 'contact', 'chat_resp_time', 'shipping_on_time',
            'authentic_rating', 'days_return', 'warranty_period',
            'product_count', 'average_rating', 'owner_name', 'recent_products'
        ]
    
    def get_title(self, obj):
        """Get translated title based on current language"""
        language_code = get_language()
        return obj.get_translated_title(language_code)
    
    def get_description(self, obj):
        """Get translated description based on current language"""
        language_code = get_language()
        return obj.get_translated_description(language_code)
    
    def get_product_count(self, obj):
        """Get total number of active products in shop"""
        return obj.products.filter(
            product_status='published',
            status=True
        ).count()
    
    def get_average_rating(self, obj):
        """Calculate average rating from all shop products"""
        products = obj.products.filter(
            product_status='published',
            status=True
        ).prefetch_related('reviews')
        
        total_ratings = 0
        total_reviews = 0
        
        for product in products:
            product_reviews = product.reviews.all()
            if product_reviews:
                total_ratings += sum([review.rating for review in product_reviews])
                total_reviews += len(product_reviews)
        
        if total_reviews == 0:
            return 0
        
        return round(total_ratings / total_reviews, 2)
    
    def get_owner_name(self, obj):
        """Get shop owner's full name"""
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return "Unknown"
    
    def get_recent_products(self, obj):
        """Get 6 most recent products from this shop"""
        from .product import ProductListSerializer
        
        recent_products = obj.products.filter(
            product_status='published',
            status=True
        ).select_related('shop', 'category', 'brand').order_by('-date')[:6]
        
        return ProductListSerializer(recent_products, many=True, context=self.context).data


class CreateShopSerializer(serializers.ModelSerializer):
    """
    Serializer for creating shops
    """
    title_translations = serializers.JSONField(required=False)
    description_translations = serializers.JSONField(required=False)
    
    class Meta:
        model = Shop
        fields = [
            'title', 'description', 'image', 'address', 'contact',
            'chat_resp_time', 'shipping_on_time', 'authentic_rating',
            'days_return', 'warranty_period', 'paypal_email',
            'title_translations', 'description_translations'
        ]
    
    def validate_title(self, value):
        """Validate shop title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Shop title cannot be empty")
        return value.strip()
    
    def validate_contact(self, value):
        """Validate contact number"""
        if value and len(value) < 10:
            raise serializers.ValidationError("Contact number must be at least 10 digits")
        return value
    
    def validate_paypal_email(self, value):
        """Validate PayPal email format"""
        if value and '@' not in value:
            raise serializers.ValidationError("Enter a valid email address")
        return value


class UpdateShopSerializer(serializers.ModelSerializer):
    """
    Serializer for updating shops
    """
    title_translations = serializers.JSONField(required=False)
    description_translations = serializers.JSONField(required=False)
    
    class Meta:
        model = Shop
        fields = [
            'title', 'description', 'image', 'address', 'contact',
            'chat_resp_time', 'shipping_on_time', 'authentic_rating',
            'days_return', 'warranty_period', 'paypal_email',
            'title_translations', 'description_translations'
        ]
    
    def validate_title(self, value):
        """Validate shop title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Shop title cannot be empty")
        return value.strip()
    
    def validate_contact(self, value):
        """Validate contact number"""
        if value and len(value) < 10:
            raise serializers.ValidationError("Contact number must be at least 10 digits")
        return value
    
    def validate_paypal_email(self, value):
        """Validate PayPal email format"""
        if value and '@' not in value:
            raise serializers.ValidationError("Enter a valid email address")
        return value