from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.database.crud import (
    get_total_sales, get_total_expenses,
    get_sales_by_date, get_today_expenses,
    get_expenses_by_date, get_products, get_customers
)
from app.services.calculator import Calculator
from config import settings

class ReportGenerator:
    def __init__(self):
        self.calculator = Calculator()

    @staticmethod
    def _format_change(change: float) -> str:
        if change > 0:
            return f"+{change:.1f}%"
        if change < 0:
            return f"{change:.1f}%"
        return "0.0%"

    @staticmethod
    def _top_item(grouped_values: dict) -> tuple[str | None, float]:
        if not grouped_values:
            return None, 0.0
        name, amount = max(grouped_values.items(), key=lambda item: item[1])
        return name, amount
    
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

    def generate_insights_report(self, db: Session, user_id: int, days: int = 7) -> str:
        """Generate trend-focused business insights with recommendations."""
        period_end = date.today()
        period_start = period_end - timedelta(days=days - 1)
        previous_end = period_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=days - 1)

        sales = get_sales_by_date(db, user_id, period_start, period_end)
        expenses = get_expenses_by_date(db, user_id, period_start, period_end)

        current_sales = self.calculator.calculate_total(sales) if sales else 0.0
        current_expenses = self.calculator.calculate_total(expenses) if expenses else 0.0
        current_profit = current_sales - current_expenses

        previous_sales = get_total_sales(db, user_id, previous_start, previous_end)
        previous_expenses = get_total_expenses(db, user_id, previous_start, previous_end)
        previous_profit = previous_sales - previous_expenses

        sales_change = self.calculator.calculate_growth(current_sales, previous_sales)
        expenses_change = self.calculator.calculate_growth(current_expenses, previous_expenses)
        profit_change = self.calculator.calculate_growth(current_profit, previous_profit)

        sales_by_product = self.calculator.group_by_category(sales, "product_name")
        sales_by_product = {
            product: amount
            for product, amount in sales_by_product.items()
            if product and str(product).strip()
        }
        top_product, top_product_revenue = self._top_item(sales_by_product)

        expense_by_category = self.calculator.group_by_category(expenses, "category")
        top_expense_category, top_expense_amount = self._top_item(expense_by_category)

        daily_profit = {}
        cursor = period_start
        while cursor <= period_end:
            day_sales = sum(sale.amount for sale in sales if sale.sale_date.date() == cursor)
            day_expenses = sum(expense.amount for expense in expenses if expense.expense_date.date() == cursor)
            daily_profit[cursor] = day_sales - day_expenses
            cursor += timedelta(days=1)

        best_day = max(daily_profit.items(), key=lambda item: item[1]) if daily_profit else None
        worst_day = min(daily_profit.items(), key=lambda item: item[1]) if daily_profit else None

        products = get_products(db, user_id)
        low_stock = [product for product in products if product.stock <= product.min_stock]

        customers = get_customers(db, user_id)
        outstanding_credit = sum(customer.credit_balance for customer in customers if customer.credit_balance > 0)

        profit_margin = (current_profit / current_sales * 100) if current_sales > 0 else 0.0
        avg_daily_sales = current_sales / days
        avg_daily_profit = current_profit / days

        report = f"🚀 *Business Insights ({days} Days)*\n"
        report += f"📅 {period_start.strftime('%d %b')} - {period_end.strftime('%d %b %Y')}\n\n"

        report += "💼 *Performance Snapshot*\n"
        report += (
            f"• Sales: {settings.CURRENCY} {current_sales:,.0f} "
            f"({self._format_change(sales_change)} vs previous {days} days)\n"
        )
        report += (
            f"• Expenses: {settings.CURRENCY} {current_expenses:,.0f} "
            f"({self._format_change(expenses_change)} vs previous {days} days)\n"
        )
        report += (
            f"• Profit: {settings.CURRENCY} {current_profit:,.0f} "
            f"({self._format_change(profit_change)} vs previous {days} days)\n"
        )
        report += f"• Profit Margin: {profit_margin:.1f}%\n"
        report += f"• Avg Daily Sales: {settings.CURRENCY} {avg_daily_sales:,.0f}\n"
        report += f"• Avg Daily Profit: {settings.CURRENCY} {avg_daily_profit:,.0f}\n\n"

        report += "🔎 *Key Drivers*\n"
        if top_product:
            report += f"• Top Product: {top_product} ({settings.CURRENCY} {top_product_revenue:,.0f})\n"
        else:
            report += "• Top Product: No sales data yet\n"

        if top_expense_category:
            report += (
                f"• Biggest Expense: {top_expense_category.title()} "
                f"({settings.CURRENCY} {top_expense_amount:,.0f})\n"
            )
        else:
            report += "• Biggest Expense: No expense data yet\n"

        if best_day:
            report += (
                f"• Best Day: {best_day[0].strftime('%a %d %b')} "
                f"({settings.CURRENCY} {best_day[1]:,.0f})\n"
            )
        if worst_day:
            report += (
                f"• Weakest Day: {worst_day[0].strftime('%a %d %b')} "
                f"({settings.CURRENCY} {worst_day[1]:,.0f})\n"
            )

        if outstanding_credit > 0:
            report += f"• Outstanding Credit: {settings.CURRENCY} {outstanding_credit:,.0f}\n"
        report += "\n"

        report += "📦 *Operations*\n"
        if low_stock:
            examples = ", ".join(f"{product.name} ({product.stock})" for product in low_stock[:3])
            report += f"• Low Stock Items: {len(low_stock)} ({examples})\n"
        else:
            report += "• Low Stock Items: 0\n"
        report += "\n"

        recommendations = []
        if current_sales == 0:
            recommendations.append("Record at least one sale daily to generate meaningful trends.")
        if current_profit < 0:
            if top_expense_category:
                recommendations.append(
                    f"Reduce {top_expense_category.title()} spending first to recover margin."
                )
            else:
                recommendations.append("Reduce costs this week until profit turns positive.")
        if sales_change < 0:
            recommendations.append("Sales are down. Try a short promo on your top-selling product.")
        if low_stock:
            recommendations.append(f"Restock {low_stock[0].name} soon to avoid stockouts.")
        if outstanding_credit > 0:
            recommendations.append("Follow up outstanding customer credit to improve cash flow.")
        if not recommendations:
            recommendations.append("Performance is healthy. Keep recording data daily to maintain momentum.")

        report += "🎯 *Recommendations*\n"
        for recommendation in recommendations[:3]:
            report += f"• {recommendation}\n"

        return report
