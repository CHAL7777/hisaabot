from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.database.crud import (
    get_user, create_product, get_products,
    get_product, update_product_stock
)
from app.database.connection import get_db_session
from config import messages, settings

router = Router()
MENU_BUTTONS = {
    "💰 Record Sale",
    "📊 Today's Report",
    "👥 Customers",
    "🧑‍💼 Team",
    "🚀 Insights",
    "💸 Record Expense",
    "📦 Inventory",
    "❓ Help",
}

class InventoryStates(StatesGroup):
    waiting_for_product = State()
    waiting_for_stock_update = State()

@router.message(Command("add_product"))
async def cmd_add_product(message: types.Message, state: FSMContext):
    """Add a new product"""
    with get_db_session() as db:
        user = get_user(db, message.from_user.id)
        
        if not user:
            await message.answer("❌ Please use /start first.")
            return
        
        # Check if command has arguments
        args = message.text.split(maxsplit=3)
        if len(args) > 1:
            # Parse arguments: /add_product name price stock
            try:
                name = args[1]
                price = float(args[2]) if len(args) > 2 else None
                stock = int(args[3]) if len(args) > 3 else 0
                
                product = create_product(
                    db=db,
                    user_id=user.id,
                    name=name,
                    selling_price=price,
                    stock=stock
                )
                
                await message.answer(
                    f"✅ Product added!\n"
                    f"• Name: {product.name}\n"
                    f"• Price: {settings.CURRENCY} {product.selling_price or 0:,.0f}\n"
                    f"• Stock: {product.stock} {product.unit}\n"
                    f"• SKU: {product.sku or 'N/A'}",
                    parse_mode="Markdown"
                )
                return
                
            except (ValueError, IndexError):
                pass  # Fall through to interactive mode
    
    await message.answer(
        "📦 *Add New Product*\n\n"
        "Enter product details in format:\n"
        "`Name Price Stock`\n\n"
        "Example: `Bread 5000 100`\n"
        "You can also enter just the name.",
        parse_mode="Markdown"
    )
    await state.set_state(InventoryStates.waiting_for_product)

@router.message(InventoryStates.waiting_for_product)
async def process_product_input(message: types.Message, state: FSMContext):
    """Process product input"""
    if message.text and message.text.startswith('/'):
        await state.clear()
        await message.answer("Product input cancelled. Run your command again.")
        return

    if message.text in MENU_BUTTONS:
        await state.clear()
        await message.answer("Product input cancelled. Tap the menu option again.")
        return

    with get_db_session() as db:
        user = get_user(db, message.from_user.id)
        
        text = message.text.strip()
        parts = text.split()
        
        try:
            if len(parts) >= 3:
                # Name, price, stock
                name = ' '.join(parts[:-2])
                price = float(parts[-2])
                stock = int(parts[-1])
            elif len(parts) == 2:
                # Name and price
                name = parts[0]
                price = float(parts[1])
                stock = 0
            else:
                # Just name
                name = text
                price = None
                stock = 0
            
            product = create_product(
                db=db,
                user_id=user.id,
                name=name,
                selling_price=price,
                stock=stock
            )
            
            response = f"✅ Product added!\n• Name: {product.name}"
            if product.selling_price:
                response += f"\n• Price: {settings.CURRENCY} {product.selling_price:,.0f}"
            response += f"\n• Stock: {product.stock} {product.unit}"
            
            await message.answer(response, parse_mode="Markdown")
            await state.clear()
            return
            
        except ValueError:
            pass
    
    await message.answer(
        "❌ Invalid format. Please use:\n"
        "`ProductName Price Stock`\n"
        "Example: `Bread 5000 100`",
        parse_mode="Markdown"
    )

@router.message(Command("products"))
@router.message(F.text.regexp(r'^📦 Inventory$'))
async def cmd_products(message: types.Message):
    """List all products"""
    with get_db_session() as db:
        user = get_user(db, message.from_user.id)
        
        if not user:
            await message.answer("❌ Please use /start first.")
            return
        
        products = get_products(db, user.id)
        
        if not products:
            await message.answer("📭 No products in inventory. Use /add_product to add some.")
            return
        
        # Group products by low stock
        low_stock = []
        normal_stock = []
        
        for product in products:
            if product.stock <= product.min_stock:
                low_stock.append(product)
            else:
                normal_stock.append(product)
        
        response = f"📦 *Inventory - {len(products)} Products*\n\n"
        
        if low_stock:
            response += "⚠️ *Low Stock Alert:*\n"
            for product in low_stock:
                response += f"• {product.name}: {product.stock} {product.unit} (min: {product.min_stock})\n"
            response += "\n"
        
        response += "*All Products:*\n"
        for product in normal_stock[:10]:  # Limit to first 10
            price_info = f"@{settings.CURRENCY} {product.selling_price:,.0f}" if product.selling_price else "Price N/A"
            response += f"• {product.name}: {product.stock} {product.unit} - {price_info}\n"
        
        if len(products) > 10:
            response += f"\n... and {len(products) - 10} more products"
        
        await message.answer(response, parse_mode="Markdown")

@router.message(Command("stock"))
async def cmd_stock(message: types.Message, state: FSMContext):
    """Check or update stock"""
    with get_db_session() as db:
        user = get_user(db, message.from_user.id)
        
        if not user:
            await message.answer("❌ Please use /start first.")
            return
        
        args = message.text.split(maxsplit=2)
        if len(args) > 1:
            # Search for product
            search_term = args[1]
            products = get_products(db, user.id)
            
            # Find matching products
            matches = [p for p in products if search_term.lower() in p.name.lower()]
            
            if not matches:
                await message.answer(f"❌ No product found with '{search_term}'")
                return
            
            if len(matches) == 1:
                product = matches[0]
                response = f"📊 *{product.name}*\n"
                response += f"• Stock: {product.stock} {product.unit}\n"
                response += f"• Min Stock: {product.min_stock}\n"
                if product.selling_price:
                    response += f"• Price: {settings.CURRENCY} {product.selling_price:,.0f}\n"
                if product.purchase_price:
                    response += f"• Cost: {settings.CURRENCY} {product.purchase_price:,.0f}\n"
                
                # Add quick actions
                response += "\n*Quick Actions:*\n"
                response += "/add_stock_" + str(product.id) + " [amount] - Add stock\n"
                response += "/sell_" + str(product.id) + " [quantity] - Record sale\n"
                
                await message.answer(response, parse_mode="Markdown")
                return
            else:
                response = f"🔍 Found {len(matches)} products:\n"
                for product in matches[:5]:
                    response += f"• {product.name}: {product.stock} {product.unit}\n"
                if len(matches) > 5:
                    response += f"... and {len(matches) - 5} more"
                await message.answer(response)
                return
    
    await message.answer(
        "📦 *Stock Management*\n\n"
        "Enter product name to check stock,\n"
        "or use /add_stock [product] [amount] to add stock.",
        parse_mode="Markdown"
    )

@router.message(Command("add_stock"))
async def cmd_add_stock(message: types.Message):
    """Add stock to product"""
    with get_db_session() as db:
        user = get_user(db, message.from_user.id)
        
        if not user:
            await message.answer("❌ Please use /start first.")
            return
        
        args = message.text.split(maxsplit=2)
        if len(args) < 3:
            await message.answer(
                "❌ Usage: /add_stock [product] [amount]\n"
                "Example: /add_stock bread 50"
            )
            return
        
        product_name = args[1]
        try:
            amount = int(args[2])
        except ValueError:
            await message.answer("❌ Amount must be a number")
            return
        
        # Find product
        products = get_products(db, user.id)
        product = next((p for p in products if product_name.lower() in p.name.lower()), None)
        
        if not product:
            await message.answer(f"❌ Product '{product_name}' not found")
            return
        
        # Update stock
        updated = update_product_stock(db, product.id, amount, operation="add")
        
        if updated:
            await message.answer(
                f"✅ Stock updated!\n"
                f"• Product: {updated.name}\n"
                f"• Added: {amount} {updated.unit}\n"
                f"• New Stock: {updated.stock} {updated.unit}"
            )
        else:
            await message.answer("❌ Failed to update stock")
