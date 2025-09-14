"""
Address serializers
"""
from rest_framework import serializers
from flame.models import Address


class AddressSerializer(serializers.ModelSerializer):
    """
    Address serializer
    """
    is_default = serializers.BooleanField(source='status', read_only=True)
    
    class Meta:
        model = Address
        fields = ['id', 'mobile', 'address', 'is_default']
        read_only_fields = ['id']
    
    def validate_mobile(self, value):
        """Validate mobile phone number"""
        if value and len(value) < 10:
            raise serializers.ValidationError("Mobile number must be at least 10 digits")
        return value
    
    def validate_address(self, value):
        """Validate address is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Address cannot be empty")
        return value.strip()


class CreateAddressSerializer(AddressSerializer):
    """
    Serializer for creating addresses
    """
    set_as_default = serializers.BooleanField(default=False, write_only=True)
    
    class Meta(AddressSerializer.Meta):
        fields = AddressSerializer.Meta.fields + ['set_as_default']


class UpdateAddressSerializer(AddressSerializer):
    """
    Serializer for updating addresses
    """
    set_as_default = serializers.BooleanField(default=False, write_only=True)
    
    class Meta(AddressSerializer.Meta):
        fields = AddressSerializer.Meta.fields + ['set_as_default']