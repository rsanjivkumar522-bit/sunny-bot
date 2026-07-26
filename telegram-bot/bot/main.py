"""
Entry point for the Telegram bot.

Modes:
  • Webhook (recommended for Render) — set WEBHOOK_URL in environment.
  • Polling (local development)      — leave WEBHOOK_URL empty.
"""
import logging
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot import config
from bot.handlers import admin, general, keywords, welcome

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def _track_chat(app: Application):
    """Middleware-like: record every chat the bot sees for broadcast."""
    async def _handler(update: Update, context):
        if update.effective_chat:
            context.bot_data.setdefault("known_chats", set()).add(
                update.effective_chat.id
            )
    return _handler


def build_application() -> Application:
    app = Application.builder().token(config.BOT_TOKEN).build()

    # ── Track chats (runs first via group 0) ─────────────────────────────────
    app.add_handler(
        MessageHandler(filters.ALL, _track_chat(app)),
        group=0,
    )

    # ── General commands ──────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start",           general.start))
    app.add_handler(CommandHandler("help",            general.help_command))
    app.add_handler(CommandHandler("ping",            general.ping))
    app.add_handler(CommandHandler("keywords",        general.list_keywords))

    # ── Admin commands ────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("warn",            admin.warn_user))
    app.add_handler(CommandHandler("warns",           admin.check_warns))
    app.add_handler(CommandHandler("resetwarn",       admin.reset_warn))
    app.add_handler(CommandHandler("mute",            admin.mute_user))
    app.add_handler(CommandHandler("unmute",          admin.unmute_user))
    app.add_handler(CommandHandler("kick",            admin.kick_user))
    app.add_handler(CommandHandler("ban",             admin.ban_user))
    app.add_handler(CommandHandler("unban",           admin.unban_user))
    app.add_handler(CommandHandler("setkeyword",      admin.set_keyword))
    app.add_handler(CommandHandler("removekeyword",   admin.remove_keyword))
    app.add_handler(CommandHandler("stats",           admin.stats))
    app.add_handler(CommandHandler("broadcast",       admin.broadcast))

    # ── Group events ──────────────────────────────────────────────────────────
    app.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome.welcome_new_member),
        group=1,
    )
    app.add_handler(
        MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, welcome.farewell_member),
        group=1,
    )

    # ── Keyword replies (group 2 — runs after commands) ───────────────────────
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, keywords.handle_keyword_reply),
        group=2,
    )

    # ── Auto-reply fallback (group 3 — private chats only) ───────────────────
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, general.auto_reply),
        group=3,
    )

    return app


def main() -> None:
    app = build_application()

    if config.WEBHOOK_URL:
        # ── Webhook mode (Render / production) ───────────────────────────────
        webhook_path = f"/webhook/{config.BOT_TOKEN}"
        webhook_url  = f"{config.WEBHOOK_URL.rstrip('/')}{webhook_path}"

        logger.info("Starting in WEBHOOK mode on port %d", config.PORT)
        logger.info("Webhook URL: %s", webhook_url)

        app.run_webhook(
            listen="0.0.0.0",
            port=config.PORT,
            url_path=webhook_path,
            webhook_url=webhook_url,
            # Render terminates TLS; the bot listens plain HTTP internally.
            allowed_updates=["message", "chat_member"],
        )
    else:
        # ── Polling mode (local dev) ──────────────────────────────────────────
        logger.info("Starting in POLLING mode (local development)")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
