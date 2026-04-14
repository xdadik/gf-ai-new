# ⚡ Quick Start Guide - Lily AI Bot

Get Lily running in 5 minutes!

## Step 1: Install Dependencies (2 min)

```bash
# Option A: Use setup script (easiest)
python setup.py

# Option B: Manual installation
pip install -r requirements.txt
```

## Step 2: Get Your Telegram Bot Token (1 min)

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name for your bot (e.g., "Lily Assistant")
4. Choose a username (must end in `bot`, e.g., `lily_ai_bot`)
5. Copy the token (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Step 3: Get Your User ID (30 sec)

1. Search for **@userinfobot** on Telegram
2. Start the bot
3. It will reply with your ID (e.g., `123456789`)

## Step 4: Configure (1 min)

Create a `.env` file:

```bash
cp .env.example .env
nano .env
```

Edit these two lines:

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
AUTHORIZED_USER_IDS=123456789
```

Save and exit (`Ctrl+X`, then `Y`, then `Enter`)

## Step 5: Run! (30 sec)

```bash
python nova_bot.py
```

You should see:
```
Lily Bot started.
```

## Step 6: Test

1. Open Telegram
2. Find your bot by the username you chose
3. Send `/start`
4. Say "Hello!"

🎉 **Done!** Lily is now running!

---

## Optional: Install Ollama for Local AI

For better privacy and offline use:

```bash
# Install Ollama (visit https://ollama.ai)
curl -fsSL https://ollama.ai/install.sh | sh  # Linux/Mac

# Pull a model
ollama pull qwen2.5-coder:3b

# Restart Lily
python nova_bot.py
```

## Common Issues

**"No module named..."**
→ Run: `pip install -r requirements.txt`

**Bot doesn't respond**
→ Check if token and user ID are correct in `.env`

**Voice messages don't work**
→ Install FFmpeg: `sudo apt install ffmpeg` (Ubuntu) or `brew install ffmpeg` (Mac)

---

**Need more help?** See [INSTALL.md](INSTALL.md) or [README.md](README.md)
