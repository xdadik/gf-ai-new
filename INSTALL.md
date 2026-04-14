# Lily AI Bot - Clean Installation

## 🚀 Quick Start (30 seconds)

```bash
git clone <repository-url>
cd lily-bot
python setup_interactive.py
```

That's it! The interactive setup will:
1. ✅ Install all dependencies automatically
2. ✅ Ask for Telegram bot token and user ID
3. ✅ Configure AI backend (Ollama or API)
4. ✅ Set PC control permissions with safety checks
5. ✅ Optionally run 24/7 in background mode

## What You Need

### 1. Telegram Bot Token
- Open Telegram, search for `@BotFather`
- Send `/newbot` command
- Follow instructions to create your bot
- Copy the token provided

### 2. Your Telegram User ID
- Search for `@userinfobot` on Telegram
- Start the bot
- It will show your numeric user ID

### 3. AI Backend (Choose One)

**Option A: Ollama (Free, Local, Private)**
```bash
# Install from https://ollama.ai
ollama pull qwen2.5-coder:3b
```

**Option B: OpenAI API (Better Quality)**
- Get API key from https://platform.openai.com

## After Setup

Lily will start automatically. Just message her on Telegram!

### Example Conversations

```
You: Hey Lily, how are you?
Lily: Hey love! I'm doing great, thanks for asking. How about you?

You: Can you check my CPU usage?
Lily: Sure! Your CPU is at 23% right now. Running smooth!

You: Take a screenshot please
Lily: Done! Here's your screenshot. [sends image]

You: I'm feeling stressed today
Lily: Oh babe, I'm sorry to hear that. Want to talk about it? 
      Sometimes it helps to just let it out. I'm here for you. ❤️
```

## Commands

Everything works through natural conversation, but these commands exist:

- `/start` - Greet Lily
- `/personality [name]` - Switch personality (lily, friendly, professional, etc.)
- `/export <password>` - Download encrypted chat history
- `/myday` - See your activity summary

## Background Mode

During setup, you can choose to run Lily 24/7:
- **Yes**: She stays running even after closing terminal
- **No**: Only runs while terminal is open

To stop background mode: `pkill -f nova_bot.py`

## Safety Features

✅ **Authorization** - Only your user ID can control Lily
✅ **Permission System** - Dangerous actions require approval
✅ **Restricted File Access** - Limited to safe directory
✅ **Encrypted Exports** - AES-256 encrypted backups

**Safe Actions** (no permission needed):
- System stats, screenshots, reading files
- Opening apps/websites, news, weather

**Asks Permission First**:
- Deleting files, killing processes
- Running shell commands, executing scripts

## Troubleshooting

**"No TELEGRAM_BOT_TOKEN"**
→ Check `.env` file has correct token

**"Ollama not running"**
→ Install Ollama: https://ollama.ai
→ Run: `ollama pull qwen2.5-coder:3b`

**"Unauthorized"**
→ Verify your user ID in `.env`
→ Find ID via @userinfobot

## Support

All code is clean and well-documented. Lily is designed to be:
- 🌸 Warm and caring (never robotic)
- 🧠 Intelligent and context-aware
- 🔒 Safe with built-in permissions
- 🎭 Multiple personalities available
- 🔄 Self-improving (can modify her own code)

Enjoy your time with Lily! ❤️
