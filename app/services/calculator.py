from typing import List, Dict, Any
from datetime import date, datetime, timedelta
from app.database.models import Sale, Expense

class Calculator:
    @staticmethod
    def calculate_total(items: List[Any]) -> float:
        """Calculate total amount from list of items with amount attribute"""
        return sum(item.amount for item in items)
    
    @staticmethod
    def calculate_profit(sales: List[Sale], expenses: List[Expense]) -> float:
        """Calculate profit: total sales - total expenses"""
        total_sales = sum(sale.amount for sale in sales)
        total_expenses = sum(expense.amount for expense in expenses)
        return total_sales - total_expenses
    
    @staticmethod
    def calculate_average(items: List[Any]) -> float:
        """Calculate average amount"""
        if not items:
            return 0.0
        total = sum(item.amount for item in items)
        return total / len(items)
    
    @staticmethod
    def calculate_daily_average(items: List[Any], days: int = 30) -> float:
        """Calculate daily average over a period"""
        if not items or days <= 0:
            return 0.0
        
        # Filter items from the last 'days' days
        cutoff_date = date.today() - timedelta(days=days)
        recent_items = [
            item for item in items 
            if hasattr(item, 'sale_date') and item.sale_date.date() >= cutoff_date
        ]
        
        if not recent_items:
            return 0.0
        
        total = sum(item.amount for item in recent_items)
        return total / days
    
    @staticmethod
    def group_by_category(items: List[Any], category_field: str = "category") -> Dict[str, float]:
        """Group items by category and sum amounts"""
        categories = {}
        for item in items:
            category = getattr(item, category_field, "Unknown")
            if category not in categories:
                categories[category] = 0.0
            categories[category] += item.amount
        return categories
    
    @staticmethod
    def calculate_growth(current_period: float, previous_period: float) -> float:
        """Calculate growth percentage"""
        if previous_period == 0:
            return 0.0 if current_period == 0 else 100.0
        return ((current_period - previous_period) / previous_period) * 100
    
    @staticmethod
    def format_currency(amount: float, currency: str = "Rp") -> str:
        """Format amount as currency"""
        if amount >= 1_000_000_000:  # Billions
            return f"{currency} {amount/1_000_000_000:,.1f}B"
        elif amount >= 1_000_000:  # Millions
            return f"{currency} {amount/1_000_000:,.1f}M"
        elif amount >= 1_000:  # Thousands
            return f"{currency} {amount/1_000:,.1f}K"
        else:
            return f"{currency} {amount:,.0f}"