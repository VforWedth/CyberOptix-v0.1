from django import template
from django.utils.translation import get_language

register = template.Library()

@register.simple_tag
def translate_field(instance, field_name):
    """Get translated field value based on current language"""
    current_lang = get_language()
    method_name = f'get_translated_{field_name}'
    
    if hasattr(instance, method_name):
        return getattr(instance, method_name)(current_lang)
    
    return getattr(instance, field_name, '')

@register.filter
def get_translation(instance, field_name):
    """Filter version of translate_field"""
    current_lang = get_language()
    method_name = f'get_translated_{field_name}'
    
    if hasattr(instance, method_name):
        return getattr(instance, method_name)(current_lang)
    
    return getattr(instance, field_name, '')