"""
Custom permission classes for API v1
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have a 'user' attribute.
        return obj.user == request.user


class IsShopOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission for shop-related objects.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if user owns the shop
        if hasattr(obj, 'shop'):
            return obj.shop.user == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow read-only access to anonymous users
    and full access to authenticated users.
    """
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS or
            request.user and request.user.is_authenticated
        )


class IsVerifiedUser(permissions.BasePermission):
    """
    Permission for email verified users only.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, 'email_verified', True)  # Default to True if field doesn't exist
        )


class IsSuperUserOrShopOwner(permissions.BasePermission):
    """
    Permission for superuser or shop owner.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_superuser or hasattr(request.user, 'shops'))
        )

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        # Check shop ownership
        if hasattr(obj, 'shop'):
            return obj.shop.user == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
            
        return False