# MicroBiz Telegram Bot

MicroBiz is a Telegram bot for small businesses to track sales, expenses, stock, customer credit, and business performance in one chat interface.

## What You Get

- Fast sales and expense recording from chat
- Inventory tracking with low-stock alerts
- Customer credit tracking and payment updates
- Multi-user team roles (owner, manager, staff) with permission control
- Daily, weekly, monthly, and custom reports
- Smart 7-day `/insights` analysis with recommendations
- Automated reminders and weekly summary notifications

## Tech Stack

- Python + `aiogram` (Telegram bot framework)
- SQLAlchemy ORM
- APScheduler (background reminders/reports)
- SQLite by default, PostgreSQL optional

## Quick Start

### 1. Clone and enter the project

```bash
git clone git@github.com:CHAL7777/hisaabot.git
cd hisaabot
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Set at least:

- `BOT_TOKEN` (required)
- `ADMIN_IDS` (optional, comma-separated Telegram IDs)
- `DB_URL` (optional; defaults to SQLite)
- `TIMEZONE` (optional; defaults to `UTC`)

Environment template:

```env
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
DB_URL=sqlite:///microbiz.db
DB_ECHO=false
TIMEZONE=UTC
```

### 5. Run the bot

```bash
python bot.py
```

On startup, tables are created automatically via SQLAlchemy `create_all`.

## Command Reference

### Core

- `/start` - Initialize bot and show keyboard
- `/help` - Show command help
- `/commands` - Alias for help
- `/settings` - Show current settings

### Sales

- `/sale` - Record sale (interactive or inline)
- `/today` - Show today’s sales summary

### Expenses

- `/expense` - Record expense (interactive or inline)
- `/expenses_today` - Show today’s expenses summary

### Inventory

- `/add_product` - Add product
- `/products` - List inventory
- `/stock` - Check product stock
- `/add_stock` - Increase stock for a product

### Customers

- `/add_customer` - Add customer
- `/customers` - List customers
- `/credit` - Add/reduce customer credit
- `/credits` - Show outstanding credits

### Reports and Analytics

- `/report` - Daily report
- `/weekly` - Weekly report
- `/monthly` - Monthly report
- `/profit` - Today’s profit
- `/custom_report` - Custom date range report
- `/insights` - Smart 7-day trend analysis and recommendations

### Team and Roles

- `/team` - List business members and roles
- `/invite <telegram_id> <role>` - Add/update member role
- `/set_role <telegram_id> <role>` - Change member role
- `/remove_member <telegram_id>` - Remove member (owner-protected)
- `/activity [limit]` - Show recent activity logs

## Quick Input Formats

### Sales examples

- `500 bread`
- `3x 500 bread`
- `500 bread 3`

### Expense examples

- `500 supplies`
- `supplies 500`

### Inventory examples

- `/add_product Bread 5000 100`
- `/add_stock Bread 20`

### Credit examples

- `/credit John 50000` (customer owes you)
- `/credit John -20000` (customer paid part of debt)

## Main Keyboard Buttons

- `💰 Record Sale`
- `💸 Record Expense`
- `📊 Today's Report`
- `📦 Inventory`
- `👥 Customers`
- `🧑‍💼 Team`
- `🚀 Insights`
- `❓ Help`

## Automated Notifications

The notifier starts with the bot and schedules:

- Daily reminder: `settings.DAILY_REPORT_HOUR` (default `20:00`)
- Weekly summary: Monday at `09:00` (`settings.WEEKLY_REPORT_DAY = 0`)

Timezone is controlled by `TIMEZONE` in `.env`.

## Database Notes

### SQLite (default)

- Default URL: `sqlite:///microbiz.db`
- Good for local/dev usage

### PostgreSQL (optional)

Set `DB_URL`, for example:

```env
DB_URL=postgresql://postgres:your_password@127.0.0.1/microbiz
```

Useful scripts:

- `python scripts/quick_test.py` - quick DB connectivity check
- `python scripts/check_schema.py` - inspect tables and schema
- `python scripts/init_db_tables.py` - create tables manually

## Project Structure

```text
microbiz_bot/
├── bot.py                     # process entrypoint
├── config.py                  # app settings and text messages
├── app/
│   ├── main.py                # bot bootstrap, routers, middleware, notifier
│   ├── database/
│   │   ├── models.py
│   │   ├── connection.py
│   │   └── crud.py
│   ├── handlers/              # Telegram command/message handlers
│   ├── services/              # parser, reports, notifier, calculator
│   └── middlewares/           # auth and throttling
├── scripts/                   # utility scripts for DB and diagnostics
└── tests/                     # unit/regression tests
```

## Development

Run tests:

```bash
pytest -q
```

Optional compile check:

```bash
python -m compileall -q app tests
```

## Troubleshooting

### Bot does not respond

- Verify `BOT_TOKEN` in `.env`
- Confirm bot is running (`python bot.py`)
- Check logs (`bot.log`)
- Send `/start` once to initialize user and keyboard

### DB connection errors

- For local development, use SQLite:
  - `DB_URL=sqlite:///microbiz.db`
- For PostgreSQL, verify credentials/host/port/database in `DB_URL`
- Run `python scripts/quick_test.py`
- See [DATABASE_TROUBLESHOOTING.md](DATABASE_TROUBLESHOOTING.md)

### Scheduled reminders not firing

- Verify `TIMEZONE` is valid
- Check bot process is continuously running
- Confirm your users have started the bot at least once

## Configuration Caveat

`CURRENCY` exists in `.env.example`, but current runtime currency is fixed in `config.py` (`Settings.CURRENCY = "Rp"`).  
If you want a different symbol immediately, update `config.py`.

## Advanced Upgrade Plan

For the full implementation blueprint for role-based access, exports/backups, profit tracking, invoices, and goal tracking, see [ADVANCED_FEATURES_BLUEPRINT.md](ADVANCED_FEATURES_BLUEPRINT.md).
