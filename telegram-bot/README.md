# Telegram Bot

A feature-rich Python Telegram bot built with [python-telegram-bot v21](https://python-telegram-bot.org/). Supports welcome messages, keyword auto-replies, admin moderation tools, and is ready for one-click deployment to [Render](https://render.com).

---

## Features

| Feature | Details |
|---|---|
| 👋 **Welcome messages** | Greets new members with a customisable message |
| 🔑 **Keyword replies** | Responds automatically when a message contains a trigger word |
| 🤖 **Auto-reply** | Replies to private messages with a configurable fallback text |
| 🛡️ **Admin commands** | Warn / mute / kick / ban users right from the chat |
| 📢 **Broadcast** | Send a message to every group the bot is in (owner only) |
| 📊 **Stats** | Live counters for messages handled, keyword hits, and welcomes |

---

## Quick Start (local development)

### 1. Clone & install dependencies

```bash
cd telegram-bot
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set BOT_TOKEN and ADMIN_IDS
```

### 3. Run the bot in polling mode

```bash
# Leave WEBHOOK_URL empty in .env for polling
python -m bot.main
```

---

## Commands

### General (anyone)

| Command | Description |
|---|---|
| `/start` | Show welcome message |
| `/help` | List all commands |
| `/keywords` | Show all active keyword triggers |
| `/ping` | Check the bot is alive |

### Admin (group admins or users in ADMIN_IDS)

| Command | Description |
|---|---|
| `/warn @user` | Issue a warning (3 warnings = auto-ban) |
| `/warns @user` | Check warning count |
| `/resetwarn @user` | Clear all warnings |
| `/mute @user` | Restrict user from sending messages |
| `/unmute @user` | Restore messaging permissions |
| `/kick @user` | Remove user (they can re-join) |
| `/ban @user` | Permanently ban a user |
| `/unban @user` | Unban a user |
| `/setkeyword keyword \| reply` | Add or update a keyword trigger |
| `/removekeyword keyword` | Delete a keyword trigger |
| `/stats` | Show bot statistics |

### Owner only (ADMIN_IDS)

| Command | Description |
|---|---|
| `/broadcast message` | Send a message to all known group chats |

---

## Configuration

All settings are controlled via environment variables.

| Variable | Required | Default | Description |
|---|---|---|---|
| `BOT_TOKEN` | ✅ | — | Token from [@BotFather](https://t.me/BotFather) |
| `WEBHOOK_URL` | ❌ | *(empty = polling)* | Your Render service URL, e.g. `https://my-bot.onrender.com` |
| `PORT` | ❌ | `8443` | Port for the webhook server (Render sets this automatically) |
| `ADMIN_IDS` | ❌ | *(empty)* | Comma-separated Telegram user IDs with full admin access |
| `AUTO_REPLY_ENABLED` | ❌ | `true` | Enable/disable auto-reply in private chats |
| `AUTO_REPLY_TEXT` | ❌ | See `.env.example` | Text sent as auto-reply in private chats |
| `WELCOME_ENABLED` | ❌ | `true` | Enable/disable welcome messages |
| `WELCOME_TEXT` | ❌ | See `.env.example` | Welcome message template. Supports `{first_name}`, `{username}`, `{group_name}` |

---

## Deploy to Render

### 1. Push this folder to a GitHub repository

Render deploys from Git. Push the contents of `telegram-bot/` (or the whole repo) to GitHub.

### 2. Create a new Web Service on Render

1. Go to [dashboard.render.com](https://dashboard.render.com) → **New** → **Web Service**
2. Connect your GitHub repository
3. Render will auto-detect `render.yaml` — click **Apply**

### 3. Set secret environment variables

In **Render dashboard → Your service → Environment**, add:

| Key | Value |
|---|---|
| `BOT_TOKEN` | Your token from BotFather |
| `WEBHOOK_URL` | `https://<your-service-name>.onrender.com` |
| `ADMIN_IDS` | Your Telegram user ID |

> **Tip:** Find your Telegram user ID by messaging [@userinfobot](https://t.me/userinfobot).

### 4. Deploy

Render will build and start the bot automatically. The webhook is registered as soon as the service starts.

> **Free plan note:** Render free web services spin down after 15 minutes of inactivity. Telegram webhooks will wake the bot back up, but the first message after a sleep may take ~30 seconds to respond. Upgrade to the **Starter** plan ($7/mo) for always-on hosting.

---

## Project Structure

```
telegram-bot/
├── bot/
│   ├── __init__.py
│   ├── config.py          # All configuration (reads from env)
│   ├── decorators.py      # @admin_only, @global_admin_only
│   ├── main.py            # Entry point — webhook or polling
│   ├── storage.py         # JSON-backed persistence (keywords, warns, stats)
│   └── handlers/
│       ├── admin.py       # Moderation commands
│       ├── general.py     # /start, /help, /ping, auto-reply
│       ├── keywords.py    # Keyword-reply matching
│       └── welcome.py     # New-member welcome handler
├── data/                  # Created at runtime — stores bot_data.json
├── .env.example           # Environment variable template
├── Procfile               # Alternative deploy (Railway, Heroku, etc.)
├── render.yaml            # Render deployment config
├── requirements.txt
└── README.md
```

---

## Adding More Keywords at Runtime

Any group admin can use the bot commands directly in Telegram — no code edits needed:

```
/setkeyword support | Please open a ticket at https://example.com/support
/setkeyword pricing | Our plans start at $9/month. Visit https://example.com/pricing
/removekeyword pricing
```

---

## Extending the Bot

- **Database**: Replace `bot/storage.py` with a Redis or PostgreSQL backend for true cross-deploy persistence.
- **Scheduled messages**: Use `Application.job_queue` to send daily announcements.
- **Conversation flows**: Use `ConversationHandler` for multi-step interactions.
- **Inline mode**: Add an `InlineQueryHandler` for in-chat search.
