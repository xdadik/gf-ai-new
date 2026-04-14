# 🚀 Lily AI Bot - Installation Guide

This guide will help you set up and run Lily AI Bot from scratch.

## Prerequisites

Before you begin, make sure you have:

1. **Python 3.9 or higher**
   ```bash
   python --version  # Should be 3.9+
   ```

2. **Git** (for cloning the repository)
   ```bash
   git --version
   ```

3. **pip** (Python package manager)
   ```bash
   pip --version
   ```

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd lily-bot
```

## Step 2: Run the Automated Setup (Recommended)

The easiest way to install everything is using the setup script:

```bash
python setup.py
```

This will:
- Check your Python version
- Create necessary directories
- Install all Python dependencies
- Create a `.env` configuration file
- Check if Ollama is running

## Step 3: Configure Your Environment

After running setup, edit the `.env` file:

```bash
nano .env
```

### Required Settings:

1. **Telegram Bot Token**
   - Open Telegram and search for `@BotFather`
   - Send `/newbot` and follow instructions
   - Copy the token and paste it in `.env`:
     ```
     TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
     ```

2. **Your Telegram User ID**
   - Search for `@userinfobot` on Telegram
   - Start the bot and it will show your ID
   - Add it to `.env`:
     ```
     AUTHORIZED_USER_IDS=123456789
     ```

### Optional Settings:

- **Ollama Configuration** (if using local AI):
  ```
  OLLAMA_MODEL=qwen2.5-coder:3b
  OLLAMA_BASE_URL=http://localhost:11434
  ```

## Step 4: Install Ollama (Optional but Recommended)

Ollama allows the bot to run AI models locally:

1. **Download Ollama**: Visit https://ollama.ai
2. **Install** following the instructions for your OS
3. **Pull a model**:
   ```bash
   ollama pull qwen2.5-coder:3b
   ```
4. **Verify it's running**:
   ```bash
   ollama list
   ```

## Step 5: Install FFmpeg (Required for Voice Messages)

### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install ffmpeg
```

### macOS:
```bash
brew install ffmpeg
```

### Windows:
Download from https://ffmpeg.org/download.html

## Step 6: Run the Bot

### Standard Mode:
```bash
python nova_bot.py
```

### With Web Dashboard:
```bash
python run_with_dashboard.py
```

You should see output like:
```
Lily Bot started.
```

## Step 7: Test the Bot

1. Open Telegram
2. Search for your bot by name
3. Send `/start`
4. Try a simple command like "Hello!"

## Troubleshooting

### Common Issues:

**"No module named 'telegram'"**
```bash
pip install -r requirements.txt
```

**"TELEGRAM_BOT_TOKEN not configured"**
- Make sure `.env` file exists and has the token

**"Ollama connection failed"**
- Ensure Ollama is running: `ollama serve`
- Check the URL in `.env` matches your Ollama instance

**"Permission denied" errors**
- On Linux/Mac: `chmod +x *.py`

**Voice messages not working**
- Install FFmpeg (see Step 5)
- Restart the bot after installation

## Manual Installation (Alternative)

If you prefer not to use the setup script:

```bash
# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p files_safe nova_memory logs

# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env

# Run the bot
python nova_bot.py
```

## Next Steps

Once your bot is running:

1. **Explore Personalities**: `/personality friendly`
2. **Try PC Control**: "Take a screenshot"
3. **Use Plugins**: `/weather`, `/calc`, etc.
4. **Check Documentation**: See README.md for full features

## Getting Help

- Check logs: `cat nova.log`
- Review PRIVACY_NOTICE.txt for privacy details
- Ensure all dependencies are installed correctly

---

**Happy chatting with Lily! 🌸**
