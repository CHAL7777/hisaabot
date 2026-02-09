# MicroBiz Telegram Bot 🤖

A comprehensive Telegram bot for micro-business management. Track sales, expenses, inventory, customers, and generate reports.

## Features

- 💰 **Sales Tracking**: Record sales with product names and quantities
- 💸 **Expense Management**: Categorize and track business expenses
- 📦 **Inventory Management**: Track stock levels with low-stock alerts
- 👥 **Customer Management**: Track customer credits and purchases
- 📊 **Reporting**: Daily, weekly, monthly, and custom reports
- 🔔 **Automated Reminders**: Daily sales reminders and low-stock alerts
- 📈 **Profit Calculation**: Automatic profit/loss calculations

## Installation

1. **Clone the repository**
```bash
<<<<<<< HEAD
git clone https://github.com/CHAL7777/hisaabot.git
cd hisaabot
=======
git clone https://github.com/yourusername/microbiz-bot.git
cd microbiz-bot
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run database migrations**
```bash
# For SQLite (development)
python -m alembic upgrade head

# For PostgreSQL (production)
export DB_URL=postgresql://user:password@localhost/microbiz
python -m alembic upgrade head
```

6. **Start the bot**
```bash
python bot.py
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Telegram Bot Token
BOT_TOKEN=your_bot_token_here

# Admin User IDs (comma-separated)
ADMIN_IDS=123456789,987654321

# Database Configuration
# SQLite (default - for development)
DB_URL=sqlite:///microbiz.db

# PostgreSQL (recommended for production)
# DB_URL=postgresql://postgres:password@localhost/microbiz

# Database Echo (debug mode)
DB_ECHO=false

# Timezone Configuration
TIMEZONE=UTC

# Currency Symbol
CURRENCY=Rp
```

### PostgreSQL Setup

For production use, PostgreSQL is recommended. Follow these steps:

1. **Install PostgreSQL**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# RHEL/CentOS
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

2. **Configure PostgreSQL Authentication**

Edit pg_hba.conf:
```bash
sudo nano /etc/postgresql/18/main/pg_hba.conf
```

Change authentication method:
```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                md5
host    all             all             127.0.0.1/32            md5
```

3. **Restart PostgreSQL**
```bash
sudo systemctl restart postgresql
```

4. **Create database and user**
```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE microbiz;
CREATE USER microbiz_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE microbiz TO microbiz_user;
\q
```

5. **Update .env file**
```env
DB_URL=postgresql://microbiz_user:your_password@localhost/microbiz
```

6. **Test connection**
```bash
python test_db.py
```

For detailed troubleshooting, see [DATABASE_TROUBLESHOOTING.md](DATABASE_TROUBLESHOOTING.md)

## Usage

### Available Commands

**Sales & Expenses:**
- `/sale [amount item]` - Record a sale
- `/expense [amount reason]` - Record expense
- `/today` - Today's summary

**Inventory:**
- `/add_product [name price stock]` - Add product
- `/products` - List all products
- `/stock [product]` - Check stock

**Customers:**
- `/add_customer [name phone]` - Add customer
- `/credit [customer amount]` - Add credit
- `/credits` - List all credits

**Reports:**
- `/report` - Daily report
- `/weekly` - Weekly report
- `/monthly` - Monthly report

**Settings:**
- `/settings` - Configure bot
- `/help` - Show this message

## Project Structure

```
microbiz_bot/
├── bot.py                    # Main bot entry point
├── config.py                 # Configuration classes
├── requirements.txt          # Python dependencies
├── test_db.py               # Database connection test
├── .env.example             # Environment template
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI main (if using)
│   ├── database/
│   │   ├── connection.py   # Database engine setup
│   │   ├── crud.py         # Database operations
│   │   └── models.py       # SQLAlchemy models
│   ├── handlers/           # Telegram bot handlers
│   │   ├── start.py
│   │   ├── sales.py
│   │   ├── expenses.py
│   │   ├── inventory.py
│   │   ├── customers.py
│   │   └── reports.py
│   ├── services/           # Business logic
│   │   ├── parser.py
│   │   ├── calculator.py
│   │   ├── reports.py
│   │   └── notifier.py
│   └── middlewares/        # Bot middlewares
│       ├── auth.py
│       └── throttling.py
├── scripts/
│   ├── database_setup.py   # Database setup helper
│   ├── quick_test.py       # Quick connection test
│   └── daily_report.py     # Daily report script
├── migrations/             # Alembic migrations
├── tests/                  # Unit tests
└── README.md
```

## Development

### Running Tests
```bash
pytest tests/
```

### Database Migrations
```bash
# Create new migration
python -m alembic revision -m "description"

# Apply migrations
python -m alembic upgrade head

# Rollback
python -m alembic downgrade -1
```

### Adding New Commands

1. Create a new handler file in `app/handlers/`
2. Register handlers in `app/main.py`
3. Add to help message in `config.py`

## Troubleshooting

### Database Connection Issues

**Error: "Ident authentication failed for user postgres"**

This is a PostgreSQL authentication issue. See [DATABASE_TROUBLESHOOTING.md](DATABASE_TROUBLESHOOTING.md) for solutions.

**Quick fix for development:**

Use SQLite instead of PostgreSQL:
```env
DB_URL=sqlite:///microbiz.db
```

### Bot Not Responding

1. Check bot token is correct in `.env`
2. Verify bot has necessary permissions
3. Check logs for errors
4. Restart the bot process

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Open a GitHub issue
- Check troubleshooting section
- Review database troubleshooting guide

>>>>>>> 031f337 (micro)
