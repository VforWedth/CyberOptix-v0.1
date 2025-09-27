"""
Category and Brand serializers
"""
from rest_framework import serializers
from flame.models import Category, Brand, Product
from ..utils import MultilingualMixin
from .product import ProductListSerializer


class CategoryDetailSerializer(serializers.ModelSerializer, MultilingualMixin):
    """
    Category detail serializer with translation support
    """
    title = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['c_id', 'title', 'image', 'image_url', 'product_count']
    
    def get_title(self, obj):
        return self.get_translated_field(obj, 'title')
    
    def get_product_count(self, obj):
        """Get count of published products in this category"""
        return obj.category.filter(
            product_status="published",
            status=True,
            in_stock=True
        ).count()
    
    def get_image_url(self, obj):
        """Get absolute URL for category image"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class CategoryListSerializer(serializers.ModelSerializer, MultilingualMixin):
    """
    Category list serializer (lighter version)
    """
    title = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['c_id', 'title', 'product_count']
    
    def get_title(self, obj):
        return self.get_translated_field(obj, 'title')
    
    def get_product_count(self, obj):
        return obj.category.filter(
            product_status="published",
            status=True
        ).count()


class BrandDetailSerializer(serializers.ModelSerializer, MultilingualMixin):
    """
    Brand detail serializer with translation support
    """
    title = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Brand
        fields = ['b_id', 'title', 'brand_image', 'image_url', 'product_count']
    
    def get_title(self, obj):
        return self.get_translated_field(obj, 'title')
    
    def get_product_count(self, obj):
        """Get count of published products for this brand"""
        return obj.brand_products.filter(
            product_status="published",
            status=True,
            in_stock=True
        ).count()
    
    def get_image_url(self, obj):
        """Get absolute URL for brand image"""
        if obj.brand_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.brand_image.url)
            return obj.brand_image.url
        return None


class BrandListSerializer(serializers.ModelSerializer, MultilingualMixin):
    """
    Brand list serializer (lighter version)
    """
    title = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Brand
        fields = ['b_id', 'title', 'product_count']
    
    def get_title(self, obj):
        return self.get_translated_field(obj, 'title')
    
    def get_product_count(self, obj):
        return obj.brand_products.filter(
            product_status="published",
            status=True
        ).count()


class CategoryWithProductsSerializer(CategoryDetailSerializer):
    """
    Category with products serializer
    """
    products = serializers.SerializerMethodField()
    
    class Meta(CategoryDetailSerializer.Meta):
        fields = CategoryDetailSerializer.Meta.fields + ['products']
    
    def get_products(self, obj):
        """Get products in this category"""
        products = obj.category.filter(
            product_status="published",
            status=True
        ).select_related('shop', 'brand').prefetch_related('reviews')[:20]
        
        return ProductListSerializer(
            products, 
            many=True, 
            context=self.context
        ).data


class BrandWithProductsSerializer(BrandDetailSerializer):
    """
    Brand with products serializer
    """
    products = serializers.SerializerMethodField()
    
    class Meta(BrandDetailSerializer.Meta):
        fields = BrandDetailSerializer.Meta.fields + ['products']
    
    def get_products(self, obj):
        """Get products for this brand"""
        products = obj.brand_products.filter(
            product_status="published",
            status=True
        ).select_related('shop', 'category').prefetch_related('reviews')[:20]
        
        return ProductListSerializer(
            products, 
            many=True, 
            context=self.context
        ).data