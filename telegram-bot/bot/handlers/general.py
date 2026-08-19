"""
General command and auto-reply handlers.
"""
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes
import yt_dlp
from google import genai

from bot import config, storage

client = genai.Client(api_key=config.GEMINI_API_KEY)

logger = logging.getLogger(__name__)


# ── /start ────────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning("/start called")

    if update.message:
        await update.message.reply_text("Bot Working ✅")
    else:
        logger.warning("update.message is None")
    



# ── /help ─────────────────────────────────────────────────────────────────────

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "*📋 Command List*\n\n"
        "*General*\n"
        "/start — Show welcome message\n"
        "/help — Show this help\n"
        "/keywords — List all keyword triggers\n"
        "/ping — Check if bot is online\n\n"
        "*Admin Commands*\n"
        "/warn @user — Warn a user (3 warns = auto-kick)\n"
        "/warns @user — Check warn count\n"
        "/resetwarn @user — Reset a user's warnings\n"
        "/mute @user — Mute a user\n"
        "/unmute @user — Unmute a user\n"
        "/kick @user — Remove user from group\n"
        "/ban @user — Ban user from group\n"
        "/unban @user — Unban a user\n"
        "/setkeyword — Add keyword reply\n"
        "/removekeyword — Remove keyword reply\n"
        "/stats — Show bot statistics\n\n"
        "*Owner Only*\n"
        "/broadcast — Send message to all groups\n",
        parse_mode="Markdown",
    )


# ── /ping ─────────────────────────────────────────────────────────────────────

# ── /dice ─────────────────────────────────────────────────────────────────────

# ── /coin ─────────────────────────────────────────────────────────────────────

# ── /8ball ────────────────────────────────────────────────────────────────────

# ── /song ─────────────────────────────────────────────────────────────────────

async def song(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "🎵 Song ka naam likho.\n\nExample:\n/song Kesariya"
        )
        return

    query = " ".join(context.args)

    await update.message.reply_text(
        f"🔎 Searching: {query}..."
    )

    try:
        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio",
            "noplaylist": True,
            "quiet": True,
            "outtmpl": "song.%(ext)s",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search = ydl.extract_info(
                f"ytsearch1:{query}",
                download=False,
            )

            if not search.get("entries"):
                await update.message.reply_text(
                    "❌ Song nahi mila."
                )
                return

            info = search["entries"][0]

            info = ydl.extract_info(
                info["webpage_url"],
                download=True,
            )

            filename = ydl.prepare_filename(info)

        with open(filename, "rb") as audio:
            await update.message.reply_audio(
                audio=audio,
                title=info.get("title", query),
                performer=info.get("uploader"),
            )

    except Exception as e:
        logger.error("Song error: %s", e)
        await update.message.reply_text(
            "❌ Song download nahi ho paya."
        )

async def eight_ball(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    answers = [
        "🎱 Yes, definitely!",
        "🎱 It is certain.",
        "🎱 Most likely.",
        "🎱 Maybe 🤔",
        "🎱 Ask again later.",
        "🎱 Probably not.",
        "🎱 No ❌",
        "🎱 Don't count on it."
    ]

    answer = random.choice(answers)
    await update.message.reply_text(answer)

async def coin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = random.choice(["Heads 🪙", "Tails 🪙"])
    await update.message.reply_text(f"🪙 {result}")

async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    number = random.randint(1, 6)
    await update.message.reply_text(f"🎲 You rolled: {number}")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🏓 Pong! I'm alive and kicking.")


# ── /keywords ─────────────────────────────────────────────────────────────────

async def list_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keywords = storage.get_keywords()
    if not keywords:
        await update.message.reply_text("📭 No keyword replies configured yet.")
        return

    lines = [f"• `{kw}` → {reply[:60]}{'…' if len(reply) > 60 else ''}"
             for kw, reply in sorted(keywords.items())]
    text = "*🔑 Active Keyword Triggers*\n\n" + "\n".join(lines)
    await update.message.reply_text(text, parse_mode="Markdown")

async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message

    if not message or not message.text:
        return

    if message.chat.type != "private":
        return

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=message.text,
        )

        reply = response.text

        if reply:
            await message.reply_text(reply)

        except Exception as e:
        logger.exception("Gemini AI ERROR")
        await message.reply_text(
            "😕 Abhi AI response nahi de pa raha. Thodi der baad try karo."
        )

# ── Auto-reply (private chats) ────────────────────────────────────────────────

async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Catch-all reply for private chat messages that weren't matched by any
    other handler. Only fires when AUTO_REPLY_ENABLED is True.
    """
    if not config.AUTO_REPLY_ENABLED:
        return

    message = update.message
    if not message:
        return

    # Only auto-reply in private chats
    if message.chat.type != "private":
        return
        
    # Ignore commands
    if message.text and message.text.startswith("/"):
        return

    await message.reply_text(config.AUTO_REPLY_TEXT)
    storage.increment_stat("messages_handled")
    logger.debug("Auto-replied to user %s", update.effective_user.id if update.effective_user else "unknown")
