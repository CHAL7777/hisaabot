import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass

class BotConfig:

    TOKEN: str = os.getenv("BOT_TOKEN")

    ADMIN_IDS: List[int] = field(default_factory=lambda: [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x])

    
@dataclass
class DatabaseConfig:
    URL: str = os.getenv("DB_URL", "sqlite:///microbiz.db")
    ECHO: bool = os.getenv("DB_ECHO", "False").lower() == "true"
    
@dataclass
class Settings:
    TIMEZONE: str = os.getenv("TIMEZONE", "UTC")
    CURRENCY: str = "Rp"
    DAILY_REPORT_HOUR: int = 20  # 8 PM
    WEEKLY_REPORT_DAY: int = 0   # Monday (0=Monday, 6=Sunday)
    
@dataclass
class Messages:
    WELCOME: str = """👋 Welcome to MicroBiz Bot!

I'll help you track your business:
• Record sales & expenses
• Manage inventory
• Track customer credits
• Generate daily reports

Use /help to see all commands."""
    
    HELP: str = """📋 *Available Commands:*

*Sales & Expenses:*
/sale [amount item] - Record a sale
/expense [amount reason] - Record expense
/today - Today's summary

*Inventory:*
/add_product [name price stock] - Add product
/products - List all products
/stock [product] - Check stock

*Customers:*
/add_customer [name phone] - Add customer
/credit [customer amount] - Add credit
/credits - List all credits

*Reports:*
/report - Daily report
/weekly - Weekly report
/monthly - Monthly report
/insights - 7-day smart business insights

*Team:*
/team - List team members
/invite [telegram_id role] - Add/update member
/set_role [telegram_id role] - Change member role
/remove_member [telegram_id] - Remove member
/activity [limit] - Recent activity log

*Settings:*
/settings - Configure bot
/help - Show this message"""
    
    ERRORS: dict = None
    
    def __post_init__(self):
        self.ERRORS = {
            "no_args": "❌ Please provide arguments. Example: `/sale 500 bread`",
            "invalid_number": "❌ Invalid number format",
            "db_error": "❌ Database error. Please try again.",
            "unauthorized": "❌ You are not authorized to use this bot.",
            "not_found": "❌ Not found.",
        }

bot_config = BotConfig()
db_config = DatabaseConfig()
settings = Settings()
messages = Messages()
