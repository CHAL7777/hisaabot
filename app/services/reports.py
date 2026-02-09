from datetime import date, datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from app.database.crud import (
    get_total_sales, get_total_expenses,
    get_sales_by_date, get_today_sales, get_today_expenses
)
from app.services.calculator import Calculator
from config import settings

class ReportGenerator:
    def __init__(self):
        self.calculator = Calculator()
    
    def generate_daily_report(self, db: Session, user_id: int, report_date: date) -> str:
        """Generate daily report"""
        # Get totals
        total_sales = get_total_sales(db, user_id, report_date, report_date)
        total_expenses = get_total_expenses(db, user_id, report_date, report_date)
        profit = total_sales - total_expenses
        
        # Get detailed transactions
        sales = get_sales_by_date(db, user_id, report_date, report_date)
        expenses = get_today_expenses(db, user_id) if report_date == date.today() else []
        
        # Generate report
        report = f"📊 *Daily Report - {report_date.strftime('%A, %d %B %Y')}*\n\n"
        
        # Summary section
        report += "💰 *Summary*\n"
        report += f"• Total Sales: {settings.CURRENCY} {total_sales:,.0f}\n"
        report += f"• Total Expenses: {settings.CURRENCY} {total_expenses:,.0f}\n"
        report += f"• Profit: {settings.CURRENCY} {profit:,.0f}\n\n"
        
        # Sales breakdown
        if sales:
            report += "🛒 *Sales Breakdown*\n"
            sales_by_product = self.calculator.group_by_category(sales, "product_name")
            for product, amount in list(sales_by_product.items())[:5]:  # Top 5
                if product:
                    percentage = (amount / total_sales * 100) if total_sales > 0 else 0
                    report += f"• {product}: {settings.CURRENCY} {amount:,.0f} ({percentage:.1f}%)\n"
            if len(sales_by_product) > 5:
                report += f"... and {len(sales_by_product) - 5} more products\n"
            report += "\n"
        
        # Expenses breakdown
        if expenses:
            report += "💸 *Expenses Breakdown*\n"
            expenses_by_category = self.calculator.group_by_category(expenses, "category")
            for category, amount in expenses_by_category.items():
                percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
                report += f"• {category.title()}: {settings.CURRENCY} {amount:,.0f} ({percentage:.1f}%)\n"
            report += "\n"
        
        # Performance indicator
        if profit > 0:
            report += "📈 *Good day!* You made a profit! 🎉\n"
        elif profit < 0:
            report += "📉 *Note:* Expenses exceeded sales today.\n"
        else:
            report += "📊 *You broke even today.*\n"
        
        return report
    
    def generate_weekly_report(self, db: Session, user_id: int, 
                             week_start: date, week_end: date) -> str:
        """Generate weekly report"""
        # Get totals
        total_sales = get_total_sales(db, user_id, week_start, week_end)
        total_expenses = get_total_expenses(db, user_id, week_start, week_end)
        profit = total_sales - total_expenses
        
        # Get daily breakdown
        daily_sales = []
        daily_expenses = []
        current_date = week_start
        
        while current_date <= week_end:
            day_sales = get_total_sales(db, user_id, current_date, current_date)
            day_expenses = get_total_expenses(db, user_id, current_date, current_date)
            daily_sales.append((current_date, day_sales))
            daily_expenses.append((current_date, day_expenses))
            current_date += timedelta(days=1)
        
        # Generate report
        report = f"📅 *Weekly Report - {week_start.strftime('%d %b')} to {week_end.strftime('%d %b %Y')}*\n\n"
        
        # Summary
        report += "💰 *Weekly Summary*\n"
        report += f"• Total Sales: {settings.CURRENCY} {total_sales:,.0f}\n"
        report += f"• Total Expenses: {settings.CURRENCY} {total_expenses:,.0f}\n"
        report += f"• Weekly Profit: {settings.CURRENCY} {profit:,.0f}\n"
        report += f"• Daily Average: {settings.CURRENCY} {profit/7:,.0f}\n\n"
        
        # Daily performance
        report += "📈 *Daily Performance*\n"
        for day_date, day_sales in daily_sales:
            day_expenses = next((de for d, de in daily_expenses if d == day_date), 0)
            day_profit = day_sales - day_expenses
            day_name = day_date.strftime('%a')
            
            emoji = "🟢" if day_profit > 0 else "🔴" if day_profit < 0 else "⚪"
            report += f"{emoji} {day_name}: {settings.CURRENCY} {day_profit:,.0f}\n"
        
        return report
    
    def generate_monthly_report(self, db: Session, user_id: int,
                              month_start: date, month_end: date) -> str:
        """Generate monthly report"""
        # Get totals
        total_sales = get_total_sales(db, user_id, month_start, month_end)
        total_expenses = get_total_expenses(db, user_id, month_start, month_end)
        profit = total_sales - total_expenses
        
        # Calculate days in month
        days_in_month = (month_end - month_start).days + 1
        
        # Generate report
        report = f"📅 *Monthly Report - {month_start.strftime('%B %Y')}*\n\n"
        
        # Summary
        report += "💰 *Monthly Summary*\n"
        report += f"• Total Sales: {settings.CURRENCY} {total_sales:,.0f}\n"
        report += f"• Total Expenses: {settings.CURRENCY} {total_expenses:,.0f}\n"
        report += f"• Monthly Profit: {settings.CURRENCY} {profit:,.0f}\n"
        report += f"• Daily Average: {settings.CURRENCY} {profit/days_in_month:,.0f}\n\n"
        
        # Performance analysis
        if profit > 0:
            profit_margin = (profit / total_sales * 100) if total_sales > 0 else 0
            report += f"✅ *Profit Margin:* {profit_margin:.1f}%\n"
            
            if profit_margin > 20:
                report += "🌟 *Excellent!* High profit margin!\n"
            elif profit_margin > 10:
                report += "👍 *Good job!* Healthy profit margin.\n"
            else:
                report += "💡 *Tip:* Consider reducing expenses to improve margin.\n"
        else:
            report += "⚠️ *Alert:* Operating at a loss this month.\n"
        
        return report
    
    def generate_custom_report(self, db: Session, user_id: int,
                             start_date: date, end_date: date) -> str:
        """Generate custom date range report"""
        total_sales = get_total_sales(db, user_id, start_date, end_date)
        total_expenses = get_total_expenses(db, user_id, start_date, end_date)
        profit = total_sales - total_expenses
        
        days = (end_date - start_date).days + 1
        
        report = f"📅 *Custom Report - {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}*\n\n"
        report += f"• Period: {days} days\n"
        report += f"• Total Sales: {settings.CURRENCY} {total_sales:,.0f}\n"
        report += f"• Total Expenses: {settings.CURRENCY} {total_expenses:,.0f}\n"
        report += f"• Net Profit: {settings.CURRENCY} {profit:,.0f}\n"
        report += f"• Daily Average: {settings.CURRENCY} {profit/days:,.0f}\n\n"
        
        # Add insights
        if days >= 7:
            weekly_avg = profit / (days / 7)
            report += f"• Weekly Average: {settings.CURRENCY} {weekly_avg:,.0f}\n"
        
        if days >= 30:
            monthly_avg = profit / (days / 30)
            report += f"• Monthly Average: {settings.CURRENCY} {monthly_avg:,.0f}\n"
        
        return report