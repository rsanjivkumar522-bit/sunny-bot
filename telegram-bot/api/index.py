import asyncio
import json
import os
import httpx

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
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        # /api/setup -> webhook setup
        if parsed.path.rstrip("/") == "/api/setup":

            key = params.get("key", [""])[0]
            expected_key = os.environ.get("WEBHOOK_SETUP_KEY", "")

            if not expected_key or key != expected_key:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Forbidden")
                return

            try:
                bot_number = int(params.get("bot", ["1"])[0])

                if bot_number < 1 or bot_number > len(config.BOT_TOKENS):
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Invalid bot number")
                    return

                token = config.BOT_TOKENS[bot_number - 1]

                host = self.headers.get("Host")
                webhook_url = f"https://{host}/api?bot={bot_number}"

                response = httpx.get(
                    f"https://api.telegram.org/bot{token}/setWebhook",
                    params={"url": webhook_url},
                    timeout=20,
                )

                self.send_response(response.status_code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(response.content)

            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())

            return

        # Normal Vercel health check
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8"
        )
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

            content_length = int(
                self.headers.get("Content-Length", "0")
            )

            body = self.rfile.read(content_length)

            data = json.loads(body.decode("utf-8"))

            asyncio.run(process_update(token, data))

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/plain; charset=utf-8"
            )
            self.end_headers()
            self.wfile.write(b"OK")

        except Exception as e:
            print("Webhook error:", repr(e))

            self.send_response(500)
            self.send_header(
                "Content-Type",
                "text/plain; charset=utf-8"
            )
            self.end_headers()
            self.wfile.write(b"Webhook error")