"""
Decorator helpers for command access control.
"""
import functools
import logging
from telegram import Update, ChatMemberAdministrator, ChatMemberOwner
from telegram.ext import ContextTypes

from bot import config

logger = logging.getLogger(__name__)


def admin_only(func):
    """
    Allow a command only if the caller is:
      1. In the ADMIN_IDS list (global bot admins), OR
      2. A chat admin / owner in the current group.
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        chat = update.effective_chat

        if user is None:
            return

        # Global bot admins
        if user.id in config.ADMIN_IDS:
            return await func(update, context, *args, **kwargs)

        # Group admins / owners
        if chat and chat.type in ("group", "supergroup"):
            member = await context.bot.get_chat_member(chat.id, user.id)
            if isinstance(member, (ChatMemberAdministrator, ChatMemberOwner)):
                return await func(update, context, *args, **kwargs)

        await update.message.reply_text("🚫 This command is for admins only.")
        logger.warning("Unauthorised admin command attempt by user %d", user.id)

    return wrapper


def global_admin_only(func):
    """Allow a command only if the caller is in ADMIN_IDS (bot owner level)."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if user is None or user.id not in config.ADMIN_IDS:
            await update.message.reply_text("🚫 This command is restricted to bot owners.")
            return
        return await func(update, context, *args, **kwargs)

    return wrapper
