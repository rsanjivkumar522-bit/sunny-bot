"""
Welcome handler — greets new members when they join a group.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot import config

logger = logging.getLogger(__name__)


async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when a new member joins the chat."""
    if not config.WELCOME_ENABLED:
        return

    message = update.message
    if not message or not message.new_chat_members:
        return

    group_name = message.chat.title or "the group"

    for member in message.new_chat_members:
        # Skip if the new member is the bot itself
        if member.id == context.bot.id:
            logger.info("Bot joined group: %s", group_name)
            await message.reply_text(
                f"👋 Hello everyone! I'm now active in *{group_name}*.\n\n"
                "I can:\n"
                "• Welcome new members\n"
                "• Reply to keywords automatically\n"
                "• Help admins manage the group\n\n"
                "Use /help to see available commands.",
                parse_mode="Markdown",
            )
            continue

        first_name = member.first_name or "there"
        username = f"@{member.username}" if member.username else first_name

        text = config.WELCOME_TEXT.format(
            first_name=first_name,
            username=username,
            group_name=group_name,
        )

        await message.reply_text(text, parse_mode="Markdown")
        logger.info("Welcomed %s in %s", first_name, group_name)


async def farewell_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Optionally acknowledge when a member leaves."""
    message = update.message
    if not message or not message.left_chat_member:
        return

    member = message.left_chat_member
    if member.id == context.bot.id:
        return  # Bot was removed

    first_name = member.first_name or "A member"
    logger.info("%s left %s", first_name, message.chat.title)
    # Uncomment to send a farewell message:
    # await message.reply_text(f"👋 {first_name} has left the group. Goodbye!")
