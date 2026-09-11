import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from telegram import Update

from bot.main import build_application
from bot import config


async def process_update(token: str, data: dict):
    app = build_application(token)

    await app.initialize()
    await app.start()

    try:
        update = Update.de_json(data=data, bot=app.bot)
        await app.process_update(update)
    finally:
        await app.stop()
        await app.shutdown()


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Sunny Bot Vercel Webhook OK")

    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            # ?bot=1 means first bot, ?bot=2 means second bot, etc.
            bot_number = int(params.get("bot", ["1"])[0])

            if bot_number < 1 or bot_number > len(config.BOT_TOKENS):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid bot number")
                return

            token = config.BOT_TOKENS[bot_number - 1]

            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length)

            data = json.loads(body.decode("utf-8"))

            asyncio.run(process_update(token, data))

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"OK")

        except Exception as e:
            print("Webhook error:", repr(e))

            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Webhook error")