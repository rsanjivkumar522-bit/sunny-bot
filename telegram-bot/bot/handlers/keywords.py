"""
Keyword-reply handler — scans messages for known keywords and responds.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot import storage, config

logger = logging.getLogger(__name__)


async def handle_keyword_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Check message text against stored keywords (case-insensitive, substring match)
    and reply with the configured response for the first match found.
    """
    message = update.message
    if not message or not message.text:
    text_lower = message.text.lower()
    # Anti-Link 
    if config.ANTI_LINK:
        if (
            "http://" in text_lower
            or "https://" in text_lower
            or "t.me/" in text_lower
            or "telegram.me/" in text_lower
            or "www." in text_lower
        ):
            await message.delete()
            await message.reply_text("🚫 Links are not allowed in this group.")
            return
    keywords = storage.get_keywords()

    for keyword, reply in keywords.items():
        if keyword in text_lower:
            await message.reply_text(reply)
            storage.increment_stat("keyword_hits")
            logger.info("Keyword '%s' matched in chat %s", keyword, message.chat_id)
            return  # First match wins
