"""
Bot configuration — loaded from environment variables.
"""
import os


def _parse_admin_ids(raw: str) -> list[int]:
    """Parse comma-separated admin IDs from an env string."""
    ids = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    return ids


# ── Required ────────────────────────────────────────────────────────────────
BOT_TOKENS: list[str] = [
    token.strip()
    for token in os.environ["BOT_TOKENS"].split(",")
    if token.strip()
]

# ── Deployment ───────────────────────────────────────────────────────────────
# On Render, set WEBHOOK_URL to your service's public URL
# e.g.  https://my-telegram-bot.onrender.com
WEBHOOK_URL: str = os.environ.get("WEBHOOK_URL", "")
PORT: int = int(os.environ.get("PORT", 8443))

# ── Admins ───────────────────────────────────────────────────────────────────
# Comma-separated list of Telegram user IDs that can use admin commands
# e.g.  ADMIN_IDS=123456789,987654321
ADMIN_IDS: list[int] = _parse_admin_ids(os.environ.get("ADMIN_IDS", ""))

# ── Bot behaviour ────────────────────────────────────────────────────────────
# Reply to every message in private chats that isn't a command
AUTO_REPLY_ENABLED: bool = os.environ.get("AUTO_REPLY_ENABLED", "true").lower() == "true"
AUTO_REPLY_TEXT: str = os.environ.get(
    "AUTO_REPLY_TEXT",
    "👋 Thanks for your message! A team member will get back to you soon.",
)

# Welcome message shown when a new member joins a group
WELCOME_ENABLED: bool = os.environ.get("WELCOME_ENABLED", "true").lower() == "true"
WELCOME_TEXT: str = os.environ.get(
    "WELCOME_TEXT",
    "👋 Welcome to {group_name}, {first_name}! Glad you're here.\n\n"
    "Please read the group rules before posting. Enjoy your stay! 🎉",
)

# ── Default keyword replies ───────────────────────────────────────────────────
# Admins can add/remove at runtime; these are the built-in defaults.
DEFAULT_KEYWORDS: dict[str, str] = {
    "hello": "👋 Hello there! How can I help you today?",
    "hi": "👋 Hi! What can I do for you?",
    "help": "ℹ️ Need help? Use /help to see available commands.",
    "price": "💰 Please visit our website or contact an admin for pricing info.",
    "rules": "📋 Please follow group rules: be respectful and stay on topic.",
    "website": "🌐 Visit our website for more information!",
    "contact": "📬 To contact us, message one of the admins directly.",
    "bye": "👋 Goodbye! Come back anytime.",
    "thanks": "😊 You're welcome! Anything else I can help with?",
    "thank you": "😊 You're very welcome! Happy to help.",
}
    # Anti-Link
ANTI_LINK = True
