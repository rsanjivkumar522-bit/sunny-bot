import asyncio
import logging

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


def build_application(token: str) -> Application:
    app = Application.builder().token(token).build()

    # ── General commands ─────────────────────────────────────────────
    app.add_handler(CommandHandler("start", general.start))
    app.add_handler(CommandHandler("help", general.help_command))
    app.add_handler(CommandHandler("ping", general.ping))
    app.add_handler(CommandHandler("keywords", general.list_keywords))
    app.add_handler(CommandHandler("dice", general.dice))

    # ── Admin commands ───────────────────────────────────────────────
    app.add_handler(CommandHandler("warn", admin.warn_user))
    app.add_handler(CommandHandler("warns", admin.check_warns))
    app.add_handler(CommandHandler("resetwarn", admin.reset_warn))
    app.add_handler(CommandHandler("mute", admin.mute_user))
    app.add_handler(CommandHandler("unmute", admin.unmute_user))
    app.add_handler(CommandHandler("kick", admin.kick_user))
    app.add_handler(CommandHandler("ban", admin.ban_user))
    app.add_handler(CommandHandler("unban", admin.unban_user))
    app.add_handler(CommandHandler("setkeyword", admin.set_keyword))
    app.add_handler(CommandHandler("removekeyword", admin.remove_keyword))
    app.add_handler(CommandHandler("stats", admin.stats))
    app.add_handler(CommandHandler("broadcast", admin.broadcast))

    # ── Name Changer ─────────────────────────────────────────────────
    app.add_handler(CommandHandler("ncstart", admin.ncstart))
    app.add_handler(CommandHandler("ncstop", admin.ncstop))

    # ── Group events ─────────────────────────────────────────────────
    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome.welcome_new_member,
        ),
        group=1,
    )

    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.LEFT_CHAT_MEMBER,
            welcome.farewell_member,
        ),
        group=1,
    )

    # ── Keyword replies ──────────────────────────────────────────────
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            keywords.handle_keyword_reply,
        ),
        group=2,
    )

    # ── Auto reply ───────────────────────────────────────────────────
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            general.auto_reply,
        ),
        group=3,
    )

    return app


async def health_server(reader, writer):
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain\r\n"
        "Content-Length: 2\r\n"
        "Connection: close\r\n"
        "\r\n"
        "OK"
    )

    writer.write(response.encode())
    await writer.drain()
    writer.close()

    try:
        await writer.wait_closed()
    except Exception:
        pass


async def main():
    port = config.PORT

    # ── Render health server ─────────────────────────────────────────
    server = await asyncio.start_server(
        health_server,
        "0.0.0.0",
        port,
    )

    logger.info("Health server running on port %s", port)

    # ── Start all 10 bots ────────────────────────────────────────────
    applications = []

    for index, token in enumerate(config.BOT_TOKENS, start=1):
        logger.info("Starting bot %d", index)

        app = build_application(token)

        await app.initialize()
        await app.start()
        await app.updater.start_polling(
            allowed_updates=Update.ALL_TYPES
        )

        applications.append(app)

        logger.info("Bot %d started successfully", index)

    logger.info(
        "ALL %d BOTS ARE RUNNING",
        len(applications),
    )

    try:
        await asyncio.Event().wait()

    finally:
        logger.info("Stopping bots...")

        for app in applications:
            try:
                await app.updater.stop()
                await app.stop()
                await app.shutdown()
            except Exception as e:
                logger.error("Shutdown error: %s", e)

        server.close()
        await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())