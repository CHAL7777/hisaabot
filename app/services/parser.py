import re
from typing import Optional, Tuple
from pydantic import BaseModel

class ParsedSale(BaseModel):
    amount: float
    item: str
    quantity: int = 1

class Parser:
    @staticmethod
    def parse_sale(text: str) -> Optional[ParsedSale]:
        """
        Parse sale messages in various formats:
        1. "500 bread" -> amount=500, item="bread", quantity=1
        2. "2x 500 bread" -> amount=1000, item="bread", quantity=2
        3. "500 bread 2" -> amount=500, item="bread", quantity=2
        4. "bread 500" -> amount=500, item="bread", quantity=1
        """
        text = text.strip()
        
        # Remove commas for thousands
        text = text.replace(',', '')
        
        # Pattern 1: "2x 500 bread"
        match = re.match(r'(\d+)x\s+(\d+\.?\d*)\s+(.+)', text)
        if match:
            quantity = int(match.group(1))
            amount = float(match.group(2))
            item = match.group(3).strip()
            return ParsedSale(amount=amount * quantity, item=item, quantity=quantity)
        
        # Pattern 2: "500 bread 2"
        match = re.match(r'(\d+\.?\d*)\s+(.+?)\s+(\d+)$', text)
        if match:
            amount = float(match.group(1))
            item = match.group(2).strip()
            quantity = int(match.group(3))
            return ParsedSale(amount=amount, item=item, quantity=quantity)
        
        # Pattern 3: "bread 500"
        match = re.match(r'(.+?)\s+(\d+\.?\d*)$', text)
        if match:
            item = match.group(1).strip()
            amount = float(match.group(2))
            return ParsedSale(amount=amount, item=item, quantity=1)
        
        # Pattern 4: "500 bread" (most common)
        match = re.match(r'(\d+\.?\d*)\s+(.+)', text)
        if match:
            amount = float(match.group(1))
            item = match.group(2).strip()
            return ParsedSale(amount=amount, item=item, quantity=1)
        
        return None
    
    @staticmethod
    def parse_expense(text: str) -> Tuple[Optional[float], Optional[str]]:
        """
        Parse expense messages:
        "500 supplies" -> (500.0, "supplies")
        "supplies 500" -> (500.0, "supplies")
        """
        text = text.strip()
        
        # Remove commas for thousands
        text = text.replace(',', '')
        
        # Pattern 1: "amount category"
        match = re.match(r'(\d+\.?\d*)\s+(.+)', text)
        if match:
            amount = float(match.group(1))
            category = match.group(2).strip()
            return amount, category
        
        # Pattern 2: "category amount"
        match = re.match(r'(.+?)\s+(\d+\.?\d*)$', text)
        if match:
            category = match.group(1).strip()
            amount = float(match.group(2))
            return amount, category
        
        return None, None
    
    @staticmethod
    def parse_product(text: str) -> Tuple[Optional[str], Optional[float], Optional[int]]:
        """
        Parse product messages:
        "bread 5000 100" -> ("bread", 5000.0, 100)
        """
        text = text.strip()
        
        # Remove commas for thousands
        text = text.replace(',', '')
        
        parts = text.split()
        if len(parts) >= 3:
            try:
                # Assume last two parts are price and stock
                price = float(parts[-2])
                stock = int(parts[-1])
                name = ' '.join(parts[:-2])
                return name, price, stock
            except ValueError:
                pass
        
        if len(parts) == 2:
            try:
                # Name and price only
                price = float(parts[-1])
                name = parts[0]
                return name, price, 0
            except ValueError:
                pass
        
        # Just name
        return text, None, 0