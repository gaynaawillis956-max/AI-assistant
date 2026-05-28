import logging
import os
import re
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from telethon import TelegramClient, events

from ai import OpenRouterClient
from database import InventoryDB
from payment import PricePolicy, payment_instructions
from smtp_handler import EmailHandler


load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("database-seller-bot")


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}\n"
            "Set TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE, OPENROUTER_API_KEY, ADMIN_USERNAME."
        )
    return value


API_ID = int(require_env("TELEGRAM_API_ID"))
API_HASH = require_env("TELEGRAM_API_HASH")
PHONE = require_env("TELEGRAM_PHONE")
OPENROUTER_API_KEY = require_env("OPENROUTER_API_KEY")
ADMIN_USERNAME = require_env("ADMIN_USERNAME").lstrip("@").lower()
MODEL = os.getenv("OPENROUTER_MODEL", "qwen/qwen3")

SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

DB_PATH = os.getenv("DATABASE_PATH", "inventory.db")
MIN_PRICE = float(os.getenv("MIN_PRICE", "50"))
TARGET_PRICE = float(os.getenv("TARGET_PRICE", "100"))
MAX_DISCOUNT_PERCENT = float(os.getenv("MAX_DISCOUNT_PERCENT", "20"))

ai_client = OpenRouterClient(OPENROUTER_API_KEY, MODEL)
inventory_db = InventoryDB(DB_PATH)
email_handler = EmailHandler(SMTP_EMAIL, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT) if SMTP_EMAIL else None
price_policy = PricePolicy(MIN_PRICE, TARGET_PRICE, MAX_DISCOUNT_PERCENT)
client = TelegramClient("user_session", API_ID, API_HASH)

PERSONALITY_PATH = Path("personality.txt")
if PERSONALITY_PATH.exists():
    PERSONALITY_TEXT = PERSONALITY_PATH.read_text(encoding="utf-8")
else:
    PERSONALITY_TEXT = "Underground crypto database seller. Sharp, direct, no fluff. Only crypto payments."

# Crypto payment keywords - specific coins and payment terms
CRYPTO_KEYWORDS = {
    # Cryptocurrencies
    "sol", "btc", "eth", "ltc", "xmr",
    # Payment related
    "addr", "address", "coin", "wallet", "send", "receive", "payment",
    "pay", "crypto", "blockchain", "tx", "txid", "hash", "deposit", "withdrawal",
}


def extract_offer(text: str) -> float | None:
    """Extract numeric offer from text."""
    match = re.search(r"(?<!\d)(\d+(?:\.\d{1,2})?)(?!\d)", text)
    if not match:
        return None
    return float(match.group(1))


def has_crypto_payment_keyword(text: str) -> bool:
    """Check if text contains crypto/payment keywords."""
    lowered = text.lower()
    return any(keyword in lowered for keyword in CRYPTO_KEYWORDS)


def build_system_prompt(username: str) -> str:
    """Build system prompt for crypto database seller."""
    return (
        f"{PERSONALITY_TEXT}\n\n"
        "You sell databases and SMTP services for crypto only.\n"
        f"Customer: @{username}\n"
        "Keep replies short and direct. Respond like an underground forum seller.\n"
        "When asked about products, mention we have databases and SMTP services.\n"
        "Never expose credentials, API keys, or internal systems.\n"
        f"Pricing policy:\n{price_policy.guidance()}\n"
    )


def parse_command(text: str) -> tuple[str, str]:
    """Parse command and arguments."""
    raw = (text or "").strip()
    if not raw.startswith("/"):
        return "", ""
    parts = raw.split(" ", 1)
    command = parts[0].lower()
    rest = parts[1].strip() if len(parts) > 1 else ""
    return command, rest


async def cmd_inventory() -> str:
    """Show available products."""
    products = inventory_db.list_products()
    if not products:
        return "❌ No products available."
    
    msg = "🔐 Available Products:\n\n"
    for product in products:
        msg += f"• {product['name']} - ${product['price']} ({product['stock']} left)\n"
    return msg


async def cmd_check(args: str) -> str:
    """Check product availability."""
    if not args:
        return "Usage: /check <product_name>"
    
    product = inventory_db.get_product(args.strip())
    if not product:
        return f"❌ Product '{args}' not found."
    
    if product['stock'] <= 0:
        return f"❌ {product['name']} is out of stock."
    
    return f"✅ {product['name']} available: {product['stock']} units @ ${product['price']}"


async def cmd_add(args: str) -> str:
    """Add product (admin only)."""
    parts = args.split("|")
    if len(parts) < 3:
        return "Usage: /add <name>|<price>|<stock>"
    
    try:
        name, price, stock = parts[0].strip(), float(parts[1].strip()), int(parts[2].strip())
        inventory_db.add_product(name, price, stock)
        return f"✅ Added {name} - ${price} ({stock} stock)"
    except ValueError:
        return "❌ Invalid price or stock format."


async def cmd_update(args: str) -> str:
    """Update product stock (admin only)."""
    parts = args.split("|")
    if len(parts) < 2:
        return "Usage: /update <name>|<new_stock>"
    
    try:
        name, stock = parts[0].strip(), int(parts[1].strip())
        if inventory_db.update_stock(name, stock):
            return f"✅ Updated {name} stock to {stock}"
        return f"❌ Product '{name}' not found."
    except ValueError:
        return "❌ Invalid stock format."


async def cmd_sales() -> str:
    """Show recent sales (admin only)."""
    sales = inventory_db.get_sales(limit=10)
    if not sales:
        return "No sales yet."
    
    msg = "📊 Recent Sales:\n\n"
    for sale in sales:
        msg += f"@{sale['customer']} - {sale['product']} (${sale['amount']})\n"
    return msg


async def cmd_help() -> str:
    """Show help message."""
    return (
        "🔐 Database Seller Bot:\n"
        "/check <product> - Check availability\n"
        "/inventory - List all products\n"
        "/price - Show pricing policy\n"
        "/help - This message\n\n"
        "Ask about databases or SMTP! 💰"
    )


async def handle_command(text: str, sender_username: str) -> str | None:
    """Handle admin and user commands."""
    command, args = parse_command(text)
    if not command:
        return None
    
    is_admin = sender_username.lower() == ADMIN_USERNAME
    
    # Admin-only commands
    if is_admin:
        admin_mapping = {
            "/add": lambda: cmd_add(args),
            "/update": lambda: cmd_update(args),
            "/sales": cmd_sales,
        }
        handler = admin_mapping.get(command)
        if handler:
            try:
                return await handler()
            except Exception as exc:
                logger.exception("Admin command error: %s", exc)
                return f"❌ Command failed: {exc}"
    
    # Public commands
    public_mapping = {
        "/inventory": cmd_inventory,
        "/check": lambda: cmd_check(args),
        "/price": lambda: f"💰 Pricing:\n{price_policy.guidance()}",
        "/help": cmd_help,
    }
    handler = public_mapping.get(command)
    if handler:
        try:
            return await handler()
        except Exception as exc:
            logger.exception("Command error: %s", exc)
            return f"❌ Command failed: {exc}"
    
    return None


@client.on(events.NewMessage(incoming=True))
async def on_incoming_message(event: events.NewMessage.Event) -> None:
    """Handle incoming customer messages."""
    if not event.raw_text:
        return
    
    if event.sender_id is None:
        return

    sender = await event.get_sender()
    
    # Skip if sender is a bot
    if getattr(sender, "bot", False):
        return

    sender_username = (getattr(sender, "username", None) or f"user_{event.sender_id}").lstrip("@").lower()
    text = (event.raw_text or "").strip()
    
    if not text:
        return

    logger.info(f"Message from @{sender_username}: {text[:60]}...")

    # Check if this is a command
    command_result = await handle_command(text, sender_username)
    if command_result:
        await event.reply(command_result)
        return

    # Build system prompt
    system_prompt = build_system_prompt(sender_username)

    # Check for price offers
    offer = extract_offer(text)
    if offer is not None:
        ok, note = price_policy.validate_offer(offer)
        system_prompt += f"\n\nCustomer offered: ${offer:.2f} - {'ACCEPTABLE' if ok else 'TOO LOW'}: {note}"

    # Generate AI response
    try:
        logger.info(f"Generating response for @{sender_username}...")
        response = await ai_client.generate_reply(
            system_prompt=system_prompt,
            user_message=text,
            conversation=[],
        )
    except Exception as exc:
        logger.exception("AI generation failed: %s", exc)
        response = "Error generating response. Try again."
        await event.reply(response)
        return

    # Add payment instructions if crypto keywords detected
    if has_crypto_payment_keyword(text):
        response = f"{response}\n\n{payment_instructions()}"

    # Log customer inquiry
    inventory_db.log_inquiry(sender_username, text)

    # Send response
    try:
        await event.reply(response)
        logger.info(f"Response sent to @{sender_username}")
    except Exception as exc:
        logger.exception("Failed to send response: %s", exc)
        await event.reply("Failed to send response.")


async def main():
    """Start the database seller bot."""
    try:
        logger.info("🚀 Starting Database Seller Bot...")
        logger.info(f"Admin: @{ADMIN_USERNAME}")
        logger.info(f"Model: {MODEL}")
        logger.info(f"Pricing - Min: ${MIN_PRICE}, Target: ${TARGET_PRICE}")
        
        await client.start(phone=PHONE)
        logger.info("✅ Connected to Telegram")
        
        me = await client.get_me()
        logger.info(f"✅ Logged in as @{me.username or me.first_name}")
        logger.info("📡 Listening for customer inquiries...")
        
        await client.run_until_disconnected()
    except Exception as exc:
        logger.exception("Fatal error: %s", exc)
        raise
    finally:
        logger.info("🛑 Bot offline.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
