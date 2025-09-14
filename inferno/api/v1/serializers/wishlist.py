"""
Wishlist serializers
"""
from rest_framework import serializers
from flame.models import Wishlist, Product
from .product import ProductListSerializer


class WishlistItemSerializer(serializers.ModelSerializer):
    """
    Wishlist item serializer
    """
    product = ProductListSerializer(read_only=True)
    added_date = serializers.DateTimeField(source='date', read_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'added_date']


class AddToWishlistSerializer(serializers.Serializer):
    """
    Serializer for adding items to wishlist
    """
    product_id = serializers.CharField()
    
    def validate_product_id(self, value):
        """Validate product exists"""
        try:
            product = Product.objects.get(p_id=value, product_status="published", status=True)
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")
    
    def validate(self, attrs):
        """Check if item already in wishlist"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            product_id = attrs['product_id']
            if Wishlist.objects.filter(
                user=request.user, 
                product__p_id=product_id
            ).exists():
                raise serializers.ValidationError("Product already in wishlist")
        return attrs