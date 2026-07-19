"""
Keyword-reply handler — scans messages for known keywords and responds.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot import storage

logger = logging.getLogger(__name__)


async def handle_keyword_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Check message text against stored keywords (case-insensitive, substring match)
    and reply with the configured response for the first match found.
    """
    message = update.message
    if not message or not message.text:
        return

    text_lower = message.text.lower()
    keywords = storage.get_keywords()

    for keyword, reply in keywords.items():
        if keyword in text_lower:
            await message.reply_text(reply)
            storage.increment_stat("keyword_hits")
            logger.info("Keyword '%s' matched in chat %s", keyword, message.chat_id)
            return  # First match wins
