"""
Address API views
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from flame.models import Address
from ..serializers.address import (
    AddressSerializer,
    CreateAddressSerializer,
    UpdateAddressSerializer
)


class AddressViewSet(viewsets.ModelViewSet):
    """
    Address ViewSet for managing user addresses
    """
    queryset = Address.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return CreateAddressSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateAddressSerializer
        else:
            return AddressSerializer
    
    def get_queryset(self):
        """Get addresses for current user"""
        return Address.objects.filter(user=self.request.user).order_by('-status', '-id')
    
    def perform_create(self, serializer):
        """Create address with current user"""
        set_as_default = serializer.validated_data.pop('set_as_default', False)
        
        # If this is the first address or set_as_default is True, make it default
        user_addresses_count = Address.objects.filter(user=self.request.user).count()
        is_default = set_as_default or user_addresses_count == 0
        
        if is_default:
            # Remove default status from other addresses
            Address.objects.filter(user=self.request.user, status=True).update(status=False)
        
        address = serializer.save(user=self.request.user, status=is_default)
        return address
    
    def perform_update(self, serializer):
        """Update address"""
        set_as_default = serializer.validated_data.pop('set_as_default', False)
        
        if set_as_default:
            # Remove default status from other addresses
            Address.objects.filter(user=self.request.user, status=True).update(status=False)
            serializer.validated_data['status'] = True
        
        address = serializer.save()
        return address
    
    def create(self, request, *args, **kwargs):
        """Create new address"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        address = self.perform_create(serializer)
        
        response_serializer = AddressSerializer(address, context={'request': request})
        
        return Response({
            'message': _('Address created successfully'),
            'address': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update address"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        address = self.perform_update(serializer)
        
        response_serializer = AddressSerializer(address, context={'request': request})
        
        return Response({
            'message': _('Address updated successfully'),
            'address': response_serializer.data
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        """Delete address"""
        instance = self.get_object()
        
        # If this is the default address, set another one as default
        if instance.status:
            other_addresses = Address.objects.filter(
                user=request.user
            ).exclude(id=instance.id).first()
            
            if other_addresses:
                other_addresses.status = True
                other_addresses.save()
        
        self.perform_destroy(instance)
        
        return Response({
            'message': _('Address deleted successfully')
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        Set address as default
        """
        address = self.get_object()
        
        # Remove default status from other addresses
        Address.objects.filter(user=request.user, status=True).update(status=False)
        
        # Set this address as default
        address.status = True
        address.save()
        
        return Response({
            'message': _('Address set as default successfully')
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def default(self, request):
        """
        Get default address
        """
        try:
            address = Address.objects.get(user=request.user, status=True)
            serializer = AddressSerializer(address, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Address.DoesNotExist:
            return Response({
                'error': _('No default address found')
            }, status=status.HTTP_404_NOT_FOUND)