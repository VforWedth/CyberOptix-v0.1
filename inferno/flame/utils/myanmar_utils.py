# flame/utils/currency.py
from decimal import Decimal
from django.core.cache import cache
from django.utils import translation
import requests
import logging

logger = logging.getLogger(__name__)

def convert_to_myanmar_numerals(text):
    """Convert English numerals to Myanmar numerals"""
    english_to_myanmar = {
        '0': '၀', '1': '၁', '2': '၂', '3': '၃', '4': '၄',
        '5': '၅', '6': '၆', '7': '၇', '8': '၈', '9': '၉'
    }
    
    result = str(text)
    for eng, myan in english_to_myanmar.items():
        result = result.replace(eng, myan)
    
    return result

def format_myanmar_currency(amount, show_kyat_symbol=True):
    """Format amount as Myanmar currency with proper separators"""
    # Format with thousand separators
    formatted = f"{amount:,.0f}"
    
    # Convert to Myanmar numerals
    formatted = convert_to_myanmar_numerals(formatted)
    
    # Add currency symbol if requested
    if show_kyat_symbol:
        formatted += " ကျပ်"
    
    return formatted

def format_usd_currency(amount):
    """Format amount as USD currency"""
    return f"${amount:,.2f}"

def format_price_display(price_usd, old_price_usd=None, language_code='en', display_preference='BOTH'):
    """
    Format price for display based on language and preference
    
    Returns a dictionary with formatted prices
    """
    from flame.models import ExchangeRate
    
    result = {}
    
    # Get exchange rate for both languages
    rate = ExchangeRate.get_current_rate('USD', 'MMK')
    
    if language_code == 'my':  # Myanmar language
        # Myanmar display - MMK primary, USD secondary
        price_mmk = price_usd * rate
        result['primary_price'] = format_myanmar_currency(price_mmk)
        
        if display_preference == 'BOTH':
            # Show USD equivalent in Myanmar numerals
            usd_formatted = f"${price_usd:,.2f}"
            result['secondary_price'] = f"({convert_to_myanmar_numerals(usd_formatted)} ဒေါ်လာ)"
        
        if old_price_usd:
            old_price_mmk = old_price_usd * rate
            result['old_price'] = format_myanmar_currency(old_price_mmk)
            
            # Calculate savings
            savings_mmk = old_price_mmk - price_mmk
            if savings_mmk > 0:
                result['savings'] = format_myanmar_currency(savings_mmk, show_kyat_symbol=False)
    
    else:  # English language
        # English display - USD primary, MMK secondary
        result['primary_price'] = format_usd_currency(price_usd)
        
        if display_preference == 'BOTH':
            # Show MMK equivalent
            price_mmk = price_usd * rate
            formatted_mmk = f"{price_mmk:,.0f}"
            result['secondary_price'] = f"{formatted_mmk} MMK"
        
        if old_price_usd:
            result['old_price'] = format_usd_currency(old_price_usd)
            
            # Calculate savings
            savings_usd = old_price_usd - price_usd
            if savings_usd > 0:
                result['savings'] = format_usd_currency(savings_usd)
    
    return result

def update_exchange_rates_from_api():
    """
    Update exchange rates from external API
    Called by cron job or admin action
    """
    from flame.models import ExchangeRate
    
    try:
        # Using exchangerate-api.com (free tier available)
        response = requests.get(
            'https://api.exchangerate-api.com/v4/latest/USD',
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        mmk_rate = Decimal(str(data['rates'].get('MMK', 3000)))
        
        # Update or create exchange rate
        exchange_rate, created = ExchangeRate.objects.update_or_create(
            currency_from='USD',
            currency_to='MMK',
            defaults={
                'rate': mmk_rate,
                'is_active': True
            }
        )
        
        # Clear cache
        cache.delete('exchange_rate_USD_MMK')
        
        logger.info(f"Exchange rate updated: 1 USD = {mmk_rate} MMK")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update exchange rates: {str(e)}")
        return False