import asyncio
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from bot import config


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            # Security key required
            key = params.get("key", [""])[0]
            if key != "SETUP123":
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Forbidden")
                return

            bot_number = int(params.get("bot", ["1"])[0])

            if bot_number < 1 or bot_number > len(config.BOT_TOKENS):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid bot number")
                return

            token = config.BOT_TOKENS[bot_number - 1]

            import httpx

            webhook_url = (
                "https://sunny-bot-api-server-yidi.vercel.app/api"
                f"?bot={bot_number}"
            )

            response = httpx.get(
                f"https://api.telegram.org/bot{token}/setWebhook",
                params={"url": webhook_url},
                timeout=20,
            )

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response.content)

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())