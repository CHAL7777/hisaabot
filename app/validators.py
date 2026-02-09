import re
from typing import Optional, Tuple

def validate_amount(text: str) -> Tuple[bool, Optional[float], Optional[str]]:
    """Validate amount input"""
    # Remove whitespace and common currency symbols
    text = text.strip().replace('$', '').replace('€', '').replace('£', '').replace('Rp', '')
    
    # Check if it's a valid number
    try:
        # Remove thousand separators
        text = text.replace(',', '')
        amount = float(text)
        
        if amount <= 0:
            return False, None, "Amount must be greater than 0"
        
        return True, amount, None
    except ValueError:
        return False, None, "Invalid amount format"

def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """Validate phone number"""
    # Remove all non-digit characters except +
    phone = re.sub(r'[^\d+]', '', phone)
    
    # Check if it starts with + (international) or 0 (local)
    if phone.startswith('+'):
        # International format
        if len(phone) < 8 or len(phone) > 15:
            return False, "Invalid international phone number"
    elif phone.startswith('0'):
        # Local format
        if len(phone) < 10 or len(phone) > 13:
            return False, "Invalid local phone number"
        # Convert to international if needed
        phone = '+62' + phone[1:]
    else:
        return False, "Phone number must start with 0 or +"
    
    return True, phone

def validate_email(email: str) -> bool:
    """Validate email address"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_product_name(name: str) -> Tuple[bool, Optional[str]]:
    """Validate product name"""
    name = name.strip()
    
    if not name:
        return False, "Product name cannot be empty"
    
    if len(name) > 200:
        return False, "Product name too long (max 200 characters)"
    
    return True, name

def validate_stock_amount(amount: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """Validate stock amount"""
    try:
        stock = int(amount)
        if stock < 0:
            return False, None, "Stock cannot be negative"
        if stock > 1_000_000:
            return False, None, "Stock amount too large"
        return True, stock, None
    except ValueError:
        return False, None, "Invalid stock amount"

def validate_date(date_str: str, format: str = "%d-%m-%Y") -> Tuple[bool, Optional[str]]:
    """Validate date string"""
    from datetime import datetime
    try:
        datetime.strptime(date_str, format)
        return True, None
    except ValueError:
        return False, f"Invalid date format. Use {format}"