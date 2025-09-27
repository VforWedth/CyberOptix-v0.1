"""
Utility functions for API v1
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.utils import translation


def custom_exception_handler(exc, context):
    """
    Custom exception handler for API responses
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            'error': {
                'status_code': response.status_code,
                'message': 'An error occurred',
                'details': response.data
            }
        }
        response.data = custom_response_data

    return response


def get_language_from_request(request):
    """
    Get language preference from request
    """
    # Try to get language from Accept-Language header or query param
    language = request.GET.get('lang') or request.META.get('HTTP_ACCEPT_LANGUAGE', 'en')
    
    # Ensure it's one of our supported languages
    if language.startswith('my'):
        return 'my'
    return 'en'


def get_translated_field(obj, field_name, language_code=None, request=None):
    """
    Get translated field value based on language preference
    """
    if language_code is None and request:
        language_code = get_language_from_request(request)
    elif language_code is None:
        language_code = translation.get_language() or 'en'
    
    # Get the translation method for the field
    method_name = f'get_translated_{field_name}'
    if hasattr(obj, method_name):
        return getattr(obj, method_name)(language_code)
    
    # Fallback to direct field access
    return getattr(obj, field_name, None)


class MultilingualMixin:
    """
    Mixin to handle multilingual content in serializers
    """
    def get_translated_field(self, obj, field_name):
        """
        Get translated field based on request language
        """
        request = self.context.get('request')
        language_code = get_language_from_request(request) if request else 'en'
        return get_translated_field(obj, field_name, language_code)