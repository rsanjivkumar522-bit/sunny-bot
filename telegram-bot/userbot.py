
import os
import logging
from telethon import TelegramClient, events

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("SUXNNY")

API_ID = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]
SESSION = os.environ.get("TG_SESSION", "sunny_userbot")

client = TelegramClient(SESSION, API_ID, API_HASH)

target_id = None

@client.on(events.NewMessage(outgoing=True, pattern=r"^/target$"))
async def set_target(event):
    global target_id

    if not event.is_reply:
        await event.reply(
            "Jis user ko select karna hai, "
            "uske message par reply karke /target bhejo."
        )
        return

    replied = await event.get_reply_message()

    if not replied.sender_id:
        await event.reply("User select nahi hua.")
        return

    target_id = replied.sender_id
    await event.reply(f"Target set: {target_id}")

@client.on(events.NewMessage(outgoing=True, pattern=r"^/stop$"))
async def stop_target(event):
    global target_id
    target_id = None
    await event.reply("Automatic replies band ho gaye.")

@client.on(events.NewMessage(incoming=True))
async def target_reply(event):
    if target_id is None or event.sender_id != target_id:
        return

    sender = await event.get_sender()
    name = getattr(sender, "first_name", None) or "Bhai"

    await event.reply(
        f"{name}, SUXNNY is here 😎👑"
    )

async def main():
    await client.start()
    me = await client.get_me()
    print(f"SUXNNY logged in as {me.username or me.id}")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
