import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient, events

from ai import OpenRouterClient
from payment import PricePolicy, payment_instructions


load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("telegram-user-copilot")


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

MIN_PRICE = float(os.getenv("MIN_PRICE", "50"))
TARGET_PRICE = float(os.getenv("TARGET_PRICE", "100"))
MAX_DISCOUNT_PERCENT = float(os.getenv("MAX_DISCOUNT_PERCENT", "20"))

ai_client = OpenRouterClient(OPENROUTER_API_KEY, MODEL)
price_policy = PricePolicy(MIN_PRICE, TARGET_PRICE, MAX_DISCOUNT_PERCENT)
client = TelegramClient("user_session", API_ID, API_HASH)

PERSONALITY_PATH = Path("personality.txt")
if PERSONALITY_PATH.exists():
    PERSONALITY_TEXT = PERSONALITY_PATH.read_text(encoding="utf-8")
else:
    PERSONALITY_TEXT = "Professional crypto assistant. Keep replies sharp, accurate, and technical."

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
    """Check if text contains crypto/payment-related keywords."""
    lowered = text.lower()
    return any(keyword in lowered for keyword in CRYPTO_KEYWORDS)


def build_system_prompt(username: str) -> str:
    """Build system prompt with crypto trading focus."""
    return (
        f"{PERSONALITY_TEXT}\n\n"
        "You are a crypto trading assistant for Telegram.\n"
        f"Speaking with @{username}.\n"
        "Respond professionally - sharp, accurate, and technical.\n"
        "Use proper crypto terminology (SOL, BTC, ETH, LTC, XMR, etc).\n"
        "Never expose API keys or sensitive data.\n"
        "Stay informed and direct.\n"
        f"Negotiation policy:\n{price_policy.guidance()}\n"
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


async def cmd_price() -> str:
    """Show current pricing policy."""
    return f"💰 Price Check:\n{price_policy.guidance()}"


async def cmd_help() -> str:
    """Show help message."""
    return (
        "🚀 Crypto Trading Copilot:\n"
        "/price - Check pricing\n"
        "/help - This message\n\n"
        "Drop your crypto questions, trades, anything! 📈"
    )


async def handle_command(text: str, sender_username: str) -> str | None:
    """Handle admin commands."""
    command, args = parse_command(text)
    if not command:
        return None
    
    # Only admin can use commands
    if sender_username.lower() != ADMIN_USERNAME:
        return None
    
    mapping = {
        "/price": cmd_price,
        "/help": cmd_help,
    }
    handler = mapping.get(command)
    if not handler:
        return None
    
    try:
        return await handler()
    except Exception as exc:
        logger.exception("Command error: %s", exc)
        return f"❌ Command failed: {exc}"


@client.on(events.NewMessage(incoming=True))
async def on_incoming_message(event: events.NewMessage.Event) -> None:
    """Handle incoming messages from crypto traders."""
    if not event.raw_text:
        return
    
    if event.sender_id is None:
        return

    sender = await event.get_sender()
    
    # Skip if sender is a bot
    if getattr(sender, "bot", False):
        return

    # Get username, fallback to user ID
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

    # Build crypto-focused system prompt
    system_prompt = build_system_prompt(sender_username)

    # Check for price offers in the message
    offer = extract_offer(text)
    policy_hint = ""
    if offer is not None:
        ok, note = price_policy.validate_offer(offer)
        policy_hint = f"\n\nPrice check ${offer:.2f}: {'✅ Accepted' if ok else '❌ Below floor'} - {note}"
        system_prompt += policy_hint

    # Generate AI response
    try:
        logger.info(f"Generating response for @{sender_username}...")
        response = await ai_client.generate_reply(
            system_prompt=system_prompt,
            user_message=text,
            conversation=[],  # No history - only current message
        )
    except Exception as exc:
        logger.exception("AI generation failed: %s", exc)
        response = "Error generating response. Try again."
        await event.reply(response)
        return

    # Add payment instructions if crypto/payment keywords detected
    if has_crypto_payment_keyword(text):
        response = f"{response}\n\n{payment_instructions()}"

    # Send response directly to chat
    try:
        await event.reply(response)
        logger.info(f"Response sent to @{sender_username}")
    except Exception as exc:
        logger.exception("Failed to send response: %s", exc)
        await event.reply("Failed to send response.")


async def main():
    """Start the Telegram crypto trading copilot."""
    try:
        logger.info("🚀 Starting Crypto Trading Copilot...")
        logger.info(f"Admin: @{ADMIN_USERNAME}")
        logger.info(f"Model: {MODEL}")
        logger.info(f"Pricing - Min: ${MIN_PRICE}, Target: ${TARGET_PRICE}, Max discount: {MAX_DISCOUNT_PERCENT}%")
        
        await client.start(phone=PHONE)
        logger.info("✅ Connected to Telegram")
        
        me = await client.get_me()
        logger.info(f"✅ Logged in as @{me.username or me.first_name}")
        logger.info("📡 Listening for crypto traders...")
        
        await client.run_until_disconnected()
    except Exception as exc:
        logger.exception("Fatal error: %s", exc)
        raise
    finally:
        logger.info("🛑 Copilot offline.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
