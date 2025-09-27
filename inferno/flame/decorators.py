from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from functools import wraps

def admin_required(view_func):
    """
    Decorator that checks if user is either a superuser or has shops (shop admin).
    Similar to Django admin but for our custom admin panel.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access the admin panel.")
            return HttpResponseRedirect(reverse('userauths:sign-in'))

        # Check if user is superuser or has admin shops
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Check if user has shops (shop admin)
        if request.user.shops.exists():
            return view_func(request, *args, **kwargs)

        # If not admin, deny access
        messages.error(request, "You don't have permission to access the admin panel.")
        return HttpResponseRedirect(reverse('flame:home'))

    return _wrapped_view

def superuser_required(view_func):
    """
    Decorator that requires superuser permissions only.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this area.")
            return HttpResponseRedirect(reverse('userauths:sign-in'))

        if not request.user.is_superuser:
            messages.error(request, "Only superuser can access this area.")
            return HttpResponseRedirect(reverse('flame:home'))

        return view_func(request, *args, **kwargs)

    return _wrapped_view

def shop_admin_required(view_func):
    """
    Decorator that checks if user has at least one shop (shop admin or superuser).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this area.")
            return HttpResponseRedirect(reverse('userauths:sign-in'))

        # Superuser has access to everything
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Check if user owns any shops
        if not request.user.shops.exists():
            messages.error(request, "You need to have a shop to access this area.")
            return HttpResponseRedirect(reverse('flame:home'))

        return view_func(request, *args, **kwargs)

    return _wrapped_view