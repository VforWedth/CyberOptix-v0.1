from django import template
from django.utils.translation import get_language
from flame.utils.myanmar_utils import convert_to_myanmar_numerals, format_myanmar_currency

register = template.Library()

@register.filter
def myanmar_number(value):
    """Convert to Myanmar numerals if language is Myanmar"""
    if get_language() == 'my':
        return convert_to_myanmar_numerals(value)
    return value

@register.filter
def myanmar_currency(value, currency='MMK'):
    """Format currency based on language"""
    if get_language() == 'my':
        return format_myanmar_currency(value, currency)
    return f"${value:,.2f}"

@register.filter
def get_translated_field(obj, field_name):
    """Get translated field value based on current language"""
    language = get_language()
    
    # Try to get language-specific field
    field_with_lang = f"{field_name}_{language}"
    if hasattr(obj, field_with_lang):
        value = getattr(obj, field_with_lang)
        if value:
            return value
    
    # Fallback to default field
    if hasattr(obj, field_name):
        return getattr(obj, field_name)
    
    return ''