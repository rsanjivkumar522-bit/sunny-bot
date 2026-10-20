
import os
import json
import logging
from pathlib import Path
from telethon import TelegramClient, events

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("SUXNNY")

API_ID = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]
SESSION = os.environ.get("TG_SESSION", "sunny_userbot")

# Settings survive restarts when the working directory is persistent.
SETTINGS_FILE = Path("userbot_settings.json")
DEFAULT_TEXT = "SUXNNY is here 😎👑"

def load_settings():
    try:
        return json.loads(SETTINGS_FILE.read_text())
    except (OSError, ValueError):
        return {"target_id": None, "reply_text": DEFAULT_TEXT, "photo": None}

settings = load_settings()
target_id = settings.get("target_id")
reply_text = settings.get("reply_text", DEFAULT_TEXT)
photo_path = settings.get("photo")

def save_settings():
    SETTINGS_FILE.write_text(json.dumps({
        "target_id": target_id,
        "reply_text": reply_text,
        "photo": photo_path,
    }))

client = TelegramClient(SESSION, API_ID, API_HASH)

@client.on(events.NewMessage(outgoing=True, pattern=r"^/target$"))
async def set_target(event):
    global target_id
    if not event.is_reply:
        await event.reply(
            "Jis user ko select karna hai, uske message par reply karke /target bhejo."
        )
        return

    replied = await event.get_reply_message()
    if not replied.sender_id:
        await event.reply("User select nahi hua.")
        return

    target_id = replied.sender_id
    save_settings()
    await event.reply("Target select ho gaya ✅")

@client.on(events.NewMessage(outgoing=True, pattern=r"^/stop$"))
async def stop_target(event):
    global target_id
    target_id = None
    save_settings()
    await event.reply("Automatic replies band ho gaye.")

@client.on(events.NewMessage(outgoing=True, pattern=r"^/settext(?:\s+[\s\S]+)?$"))
async def set_text(event):
    global reply_text
    text = event.raw_text.partition(" ")[2].strip()
    if not text:
        await event.reply("Use: /settext Tumhara custom message")
        return
    reply_text = text
    save_settings()
    await event.reply("Custom reply text save ho gaya ✅")

@client.on(events.NewMessage(outgoing=True, pattern=r"^/setphoto$"))
async def set_photo(event):
    global photo_path
    if not event.is_reply:
        await event.reply(
            "Apni photo par reply karke /setphoto bhejo."
        )
        return

    replied = await event.get_reply_message()
    if not replied.photo:
        await event.reply("Reply kiya hua message photo hona chahiye.")
        return

    path = await replied.download_media(file="userbot_photo.jpg")
    if not path:
        await event.reply("Photo download nahi ho paayi.")
        return

    photo_path = path
    save_settings()
    await event.reply("Photo save ho gayi ✅")

@client.on(events.NewMessage(incoming=True))
async def target_reply(event):
    if target_id is None or event.sender_id != target_id:
        return

    # Reply only in groups, to avoid replying in unrelated private chats.
    if not event.is_group:
        return

    if photo_path and Path(photo_path).is_file():
        await client.send_file(
            event.chat_id,
            photo_path,
            caption=reply_text,
            reply_to=event.id,
        )
    else:
        await event.reply(reply_text)

async def main():
    await client.start()
    me = await client.get_me()
    print(f"SUXNNY logged in as {me.username or me.id}")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
