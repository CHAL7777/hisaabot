import re
from typing import Optional

def format_currency(amount: float, currency: str = "Rp", decimal_places: int = 0) -> str:
    """Format amount as currency string"""
    if decimal_places > 0:
        format_str = f",.{decimal_places}f"
    else:
        format_str = ",.0f"
    
    formatted_amount = format(amount, format_str)
    return f"{currency} {formatted_amount}"

def parse_currency(text: str) -> Optional[float]:
    """Parse currency string to float"""
    # Remove currency symbols and thousand separators
    text = re.sub(r'[^\d.,-]', '', text)
    
    # Handle negative numbers
    is_negative = '-' in text
    text = text.replace('-', '')
    
    # Determine decimal separator
    if ',' in text and '.' in text:
        # If both exist, last one is decimal
        if text.rfind(',') > text.rfind('.'):
            text = text.replace('.', '').replace(',', '.')
        else:
            text = text.replace(',', '')
    elif ',' in text:
        # Comma as decimal or thousand separator?
        if text.count(',') == 1 and len(text.split(',')[1]) <= 2:
            # Probably decimal
            text = text.replace(',', '.')
        else:
            # Probably thousand separator
            text = text.replace(',', '')
    
    try:
        amount = float(text)
        if is_negative:
            amount = -amount
        return amount
    except ValueError:
        return None

def format_percentage(value: float, decimal_places: int = 1) -> str:
    """Format percentage"""
    return f"{value:.{decimal_places}f}%"

def format_compact_currency(amount: float, currency: str = "Rp") -> str:
    """Format large amounts in compact form (K, M, B)"""
    if amount >= 1_000_000_000:
        return f"{currency} {amount/1_000_000_000:.1f}B"
    elif amount >= 1_000_000:
        return f"{currency} {amount/1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"{currency} {amount/1_000:.1f}K"
    else:
        return f"{currency} {amount:,.0f}"