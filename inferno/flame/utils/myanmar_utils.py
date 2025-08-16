def convert_to_myanmar_numerals(number):
    """Convert English numerals to Myanmar numerals"""
    english_to_myanmar = {
        '0': '၀', '1': '၁', '2': '၂', '3': '၃', '4': '၄',
        '5': '၅', '6': '၆', '7': '၇', '8': '၈', '9': '၉'
    }
    
    number_str = str(number)
    for eng, myan in english_to_myanmar.items():
        number_str = number_str.replace(eng, myan)
    
    return number_str

def format_myanmar_currency(amount, currency='MMK'):
    """Format currency for Myanmar"""
    if currency == 'MMK':
        # Format as Myanmar Kyat
        formatted = f"{amount:,.0f} ကျပ်"
        return convert_to_myanmar_numerals(formatted)
    else:
        # Keep USD format
        return f"${amount:,.2f}"