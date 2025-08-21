# flame/templatetags/myanmar_filter.py
from django import template
from django.utils import translation
from flame.utils.myanmar_utils import (
    format_price_display,
    convert_to_myanmar_numerals,
    format_myanmar_currency,
    format_usd_currency
)
import logging
from decimal import Decimal

register = template.Library()
logger = logging.getLogger(__name__)

@register.filter
def to_myanmar_numerals(value):
    """Convert to Myanmar numerals"""
    return convert_to_myanmar_numerals(value)

@register.filter
def format_price(product, language_code=None):
    """Format product price based on language"""
    if language_code is None:
        language_code = translation.get_language()
    
    price_data = get_price_display(product, language_code)
    return price_data.get('primary_price', f"${product.price:,.2f}")

# myanmar_filter.py
@register.simple_tag
def get_price_display(product_or_price, old_price=None, language_code=None):
    """Get price display information - handles both Product objects and raw prices"""
    if language_code is None:
        language_code = translation.get_language()
    
    try:
        from flame.models import ExchangeRate
        
        # Check if we received a Product object or a raw price
        if hasattr(product_or_price, 'price'):
            # It's a Product object
            price_usd = product_or_price.price
            old_price_usd = getattr(product_or_price, 'old_price', None)
        else:
            # It's a raw price value
            price_usd = product_or_price
            old_price_usd = old_price
        
        # Rest of the function remains the same...
        result = {}
        
        if language_code == 'my':
            # Get exchange rate with fallback
            try:
                rate = ExchangeRate.get_current_rate('USD', 'MMK')
            except Exception as e:
                logger.error(f"Error getting exchange rate: {e}")
                rate = Decimal('3500')  # Fallback rate
            
            # Convert to MMK
            price_mmk = price_usd * rate
            formatted = f"{price_mmk:,.0f}"
            result['primary_price'] = to_myanmar_numerals(formatted) + " ကျပ်"
            
            # Add USD equivalent
            usd_formatted = f"${price_usd:,.2f}"
            result['secondary_price'] = f"({to_myanmar_numerals(usd_formatted)})"
            
            if old_price_usd:
                old_price_mmk = old_price_usd * rate
                old_formatted = f"{old_price_mmk:,.0f}"
                result['old_price'] = to_myanmar_numerals(old_formatted) + " ကျပ်"
        else:
            # English display
            result['primary_price'] = f"${price_usd:,.2f}"
            
            if old_price_usd:
                result['old_price'] = f"${old_price_usd:,.2f}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_price_display: {e}")
        # Return simple USD display as fallback
        fallback_price = product_or_price if not hasattr(product_or_price, 'price') else product_or_price.price
        return {
            'primary_price': f"${fallback_price:,.2f}",
            'old_price': f"${old_price:,.2f}" if old_price else None
        }


@register.filter
def multiply(value, arg):
    """Multiply filter for templates"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.simple_tag(takes_context=True)
def get_cart_total(context, in_mmk=False):
    """Calculate cart total in USD or MMK"""
    from flame.models import ExchangeRate
    
    cart = context.get('cart', {})
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    
    if in_mmk:
        rate = ExchangeRate.get_current_rate('USD', 'MMK')
        total_mmk = total * rate
        return format_myanmar_currency(total_mmk)
    
    return format_usd_currency(total)

@register.simple_tag
def format_currency_amount(amount, language_code=None):
    """Format any USD amount based on language with proper Myanmar numerals"""
    if language_code is None:
        language_code = translation.get_language()
    
    try:
        from flame.models import ExchangeRate
        
        if language_code == 'my':
            # Get exchange rate with fallback
            try:
                rate = ExchangeRate.get_current_rate('USD', 'MMK')
            except Exception as e:
                logger.error(f"Error getting exchange rate: {e}")
                rate = Decimal('3500')  # Fallback rate
            
            # Convert to MMK
            price_mmk = amount * rate
            formatted_mmk = f"{price_mmk:,.0f}"
            
            # Format USD with Myanmar numerals
            usd_formatted = f"${amount:,.2f}"
            
            return {
                'primary': to_myanmar_numerals(formatted_mmk) + " ကျပ်",
                'secondary': f"({to_myanmar_numerals(usd_formatted)} ဒေါ်လာ)"
            }
        else:
            # English display
            return {
                'primary': f"${amount:,.2f}",
                'secondary': None
            }
            
    except Exception as e:
        logger.error(f"Error in format_currency_amount: {e}")
        # Return simple USD display as fallback
        return {
            'primary': f"${amount:,.2f}",
            'secondary': None
        }