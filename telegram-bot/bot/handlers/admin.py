"""
Admin command handlers — warn, mute, kick, ban, broadcast, and keyword management.
"""
import logging
import asyncio
from telegram import Update, ChatPermissions
from telegram.error import BadRequest
from telegram.ext import ContextTypes, ConversationHandler

from bot import storage
from bot.decorators import admin_only, global_admin_only

logger = logging.getLogger(__name__)

MAX_WARNS = 3  # auto-kick after this many warnings

# ── Name Changer ─────────────────────────────────────────

NC_RUNNING = {}
NC_TASKS = {}

NC_NAMES = [
    "🔥 Name 1 🔥",
    "⚡ Name 2 ⚡",
    "👑 Name 3 👑",
    "💀 Name 4 💀",
]
async def nc_loop(context, chat_id, base_name):
    while NC_RUNNING.get(chat_id, False):
        try:
            await context.bot.set_chat_title(chat_id, base_name)
        except Exception as e:
            logger.error(f"NC Error: {e}")

        await asyncio.sleep(3)

@admin_only
async def ncstart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    base_name = " ".join(context.args)

    if NC_RUNNING.get(chat_id):
        await update.message.reply_text("⚠️ Name Changer is already running.")
        return
    
    if not context.args:
    await update.message.reply_text("Usage: /ncstart <text>")
    return
    
    NC_RUNNING[chat_id] = True

    task = asyncio.create_task(nc_loop(context, chat_id, base_name))
    NC_TASKS[chat_id] = task

    await update.message.reply_text("✅ Name Changer Started.")

@admin_only
async def ncstop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not NC_RUNNING.get(chat_id):
        await update.message.reply_text("⚠️ Name Changer is not running.")
        return

    NC_RUNNING[chat_id] = False

    task = NC_TASKS.pop(chat_id, None)
    if task:
        task.cancel()

    await update.message.reply_text("🛑 Name Changer Stopped.")

# ── Helpers ───────────────────────────────────────────────────────────────────

async def _resolve_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Return (user_id, first_name) of the target user from a reply or @mention.
    Returns (None, None) and sends an error message if no valid target found.
    """
    message = update.message

    # Reply-based target
    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        return u.id, u.first_name

    # Mention/username/ID as argument
    if context.args:
        arg = context.args[0].lstrip("@")
        try:
            uid = int(arg)
            member = await context.bot.get_chat_member(message.chat_id, uid)
            return uid, member.user.first_name
        except (ValueError, BadRequest):
            pass
        # Try username lookup (works only if the user is in the chat)
        try:
            # Telegram doesn't support username→id directly; hint user to reply
            pass
        except Exception:
            pass
        await message.reply_text(
            "⚠️ Could not find that user. Reply to their message or provide a numeric user ID."
        )
        return None, None

    await message.reply_text(
        "⚠️ Please reply to a user's message or provide their @username/ID.\n"
        "Example: `/warn @username` or reply to their message and use `/warn`",
        parse_mode="Markdown",
    )
    return None, None


# ── /warn ─────────────────────────────────────────────────────────────────────

@admin_only
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, first_name = await _resolve_target(update, context)
    if user_id is None:
        return

    chat_id = update.message.chat_id
    count = storage.add_warn(user_id)

    if count >= MAX_WARNS:
        try:
            await context.bot.ban_chat_member(chat_id, user_id)
            storage.reset_warns(user_id)
            await update.message.reply_text(
                f"⛔ {first_name} has been *banned* after reaching {MAX_WARNS} warnings.",
                parse_mode="Markdown",
            )
            logger.info("Auto-banned user %d after %d warns", user_id, MAX_WARNS)
        except BadRequest as e:
            await update.message.reply_text(f"❌ Could not ban: {e}")
    else:
        await update.message.reply_text(
            f"⚠️ *{first_name}* has been warned. "
            f"({count}/{MAX_WARNS} warnings)\n\n"
            f"{'One more warn and they will be banned!' if count == MAX_WARNS - 1 else ''}",
            parse_mode="Markdown",
        )
        logger.info("Warned user %d (%d/%d)", user_id, count, MAX_WARNS)


# ── /warns ────────────────────────────────────────────────────────────────────

@admin_only
async def check_warns(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, first_name = await _resolve_target(update, context)
    if user_id is None:
        return

    count = storage.get_warns(user_id)
    await update.message.reply_text(
        f"📋 *{first_name}* has *{count}/{MAX_WARNS}* warnings.",
        parse_mode="Markdown",
    )


# ── /resetwarn ────────────────────────────────────────────────────────────────

@admin_only
async def reset_warn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, first_name = await _resolve_target(update, context)
    if user_id is None:
        return

    storage.reset_warns(user_id)
    await update.message.reply_text(
        f"✅ Warnings for *{first_name}* have been reset.",
        parse_mode="Markdown",
    )


# ── /mute ─────────────────────────────────────────────────────────────────────

@admin_only
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, first_name = await _resolve_target(update, context)
    if user_id is None:
        return

    chat_id = update.message.chat_id
    try:
        await context.bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
            ),
        )
        storage.set_muted(user_id, True)
        await update.message.reply_text(
            f"🔇 *{first_name}* has been muted.",
            parse_mode="Markdown",
        )
        logger.info("Muted user %d in chat %d", user_id, chat_id)
    except BadRequest as e:
        await update.message.reply_text(f"❌ Could not mute: {e}")


# ── /unmute ───────────────────────────────────────────────────────────────────

@admin_only
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, first_name = await _resolve_target(update, context)
    if user_id is None:
        return

    chat_id = update.message.chat_id
    try:
        await context.bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_send_polls=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False,
            ),
        )
        storage.set_muted(user_id, False)
        await update.message.reply_text(
            f"🔊 *{first_name}* has been unmuted.",
            parse_mode="Markdown",
        )
    except BadRequest as e:
        await update.message.reply_text(f"❌ Could not unmute: {e}")


# ── /kick ─────────────────────────────────────────────────────────────────────

@admin_only
async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, first_name = await _resolve_target(update, context)
    if user_id is None:
        return

    chat_id = update.message.chat_id
    try:
        await context.bot.ban_chat_member(chat_id, user_id)
        await context.bot.unban_chat_member(chat_id, user_id)  # allows re-joining
        await update.message.reply_text(
            f"👢 *{first_name}* has been kicked from the group.",
            parse_mode="Markdown",
        )
        logger.info("Kicked user %d from chat %d", user_id, chat_id)
    except BadRequest as e:
        await update.message.reply_text(f"❌ Could not kick: {e}")


# ── /ban ──────────────────────────────────────────────────────────────────────

@admin_only
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, first_name = await _resolve_target(update, context)
    if user_id is None:
        return

    chat_id = update.message.chat_id
    try:
        await context.bot.ban_chat_member(chat_id, user_id)
        await update.message.reply_text(
            f"⛔ *{first_name}* has been permanently banned.",
            parse_mode="Markdown",
        )
        logger.info("Banned user %d from chat %d", user_id, chat_id)
    except BadRequest as e:
        await update.message.reply_text(f"❌ Could not ban: {e}")


# ── /unban ────────────────────────────────────────────────────────────────────

@admin_only
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, first_name = await _resolve_target(update, context)
    if user_id is None:
        return

    chat_id = update.message.chat_id
    try:
        await context.bot.unban_chat_member(chat_id, user_id)
        await update.message.reply_text(
            f"✅ *{first_name}* has been unbanned.",
            parse_mode="Markdown",
        )
    except BadRequest as e:
        await update.message.reply_text(f"❌ Could not unban: {e}")


# ── /setkeyword ───────────────────────────────────────────────────────────────

@admin_only
async def set_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usage: /setkeyword <keyword> | <reply text>"""
    if not context.args:
        await update.message.reply_text(
            "📝 Usage: `/setkeyword keyword | Reply text`\n\n"
            "Example:\n`/setkeyword discount | We offer 10% off for new members!`",
            parse_mode="Markdown",
        )
        return

    full_text = " ".join(context.args)
    if "|" not in full_text:
        await update.message.reply_text(
            "⚠️ Please separate the keyword and reply with a pipe `|`.\n"
            "Example: `/setkeyword price | Our pricing starts at $9/month`",
            parse_mode="Markdown",
        )
        return

    keyword, _, reply = full_text.partition("|")
    keyword = keyword.strip().lower()
    reply = reply.strip()

    if not keyword or not reply:
        await update.message.reply_text("⚠️ Both keyword and reply text are required.")
        return

    storage.set_keyword(keyword, reply)
    await update.message.reply_text(
        f"✅ Keyword saved!\n\n*Trigger:* `{keyword}`\n*Reply:* {reply}",
        parse_mode="Markdown",
    )
    logger.info("Keyword set: '%s'", keyword)


# ── /removekeyword ────────────────────────────────────────────────────────────

@admin_only
async def remove_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usage: /removekeyword <keyword>"""
    if not context.args:
        await update.message.reply_text(
            "📝 Usage: `/removekeyword <keyword>`",
            parse_mode="Markdown",
        )
        return

    keyword = " ".join(context.args).strip().lower()
    removed = storage.remove_keyword(keyword)

    if removed:
        await update.message.reply_text(
            f"🗑️ Keyword `{keyword}` has been removed.",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"⚠️ Keyword `{keyword}` not found.",
            parse_mode="Markdown",
        )


# ── /stats ────────────────────────────────────────────────────────────────────

@admin_only
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    s = storage.get_stats()
    kw_count = len(storage.get_keywords())
    await update.message.reply_text(
        "📊 *Bot Statistics*\n\n"
        f"💬 Messages handled: `{s.get('messages_handled', 0)}`\n"
        f"🔑 Keyword hits: `{s.get('keyword_hits', 0)}`\n"
        f"👋 Welcomes sent: `{s.get('welcomes_sent', 0)}`\n"
        f"📝 Active keywords: `{kw_count}`\n",
        parse_mode="Markdown",
    )


# ── /broadcast ────────────────────────────────────────────────────────────────

@global_admin_only
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Usage: /broadcast <message text>
    Sends a message to every chat the bot has stored.
    For now this forwards the message back; wire up a chat-id registry if needed.
    """
    if not context.args:
        await update.message.reply_text(
            "📢 Usage: `/broadcast Your message here`",
            parse_mode="Markdown",
        )
        return

    text = " ".join(context.args)
    # context.bot_data["known_chats"] should be populated in the message handler
    known_chats: set = context.bot_data.get("known_chats", set())

    if not known_chats:
        await update.message.reply_text(
            "📭 No chats to broadcast to yet. Add the bot to groups first."
        )
        return

    success, failed = 0, 0
    for chat_id in known_chats:
        try:
            await context.bot.send_message(
                chat_id,
                f"📢 *Announcement*\n\n{text}",
                parse_mode="Markdown",
            )
            success += 1
        except Exception as e:
            logger.warning("Broadcast failed for chat %s: %s", chat_id, e)
            failed += 1

    await update.message.reply_text(
        f"📢 Broadcast complete.\n✅ Sent: {success}\n❌ Failed: {failed}"
    )
