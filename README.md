# 🌸 Lily AI Bot

A powerful, intelligent Telegram bot with advanced PC control capabilities, powered by Ollama AI and featuring multiple personality modes. Lily is your caring AI companion who can help with everything from system tasks to meaningful conversations.

## ✨ Features

### 🤖 AI-Powered Conversations
- **Multiple Personalities**: Switch between 12+ distinct personalities (Friendly, Professional, Playful, Commander, Scholar, Sassy, Creative, Zen, Charming, Companion, Mentor, Partner)
- **Natural Language Processing**: Understands context and maintains conversation flow
- **Voice Message Support**: Automatic transcription using Whisper AI
- **Memory System**: Remembers important details about you while respecting privacy

### 💻 Advanced PC Control
Control your computer through natural language:
- 📸 Screenshot capture and sharing
- 📋 Clipboard management (read/write)
- 🖥️ Process monitoring and management
- 📁 File operations (browse, organize, manage)
- 🚀 Application launching
- 📊 Real-time system statistics
- 🔍 Web search integration
- ⏰ Timers and reminders

### 🔒 Security Features

#### End-to-End Encryption
- All messages encrypted before transmission
- Unique encryption keys per user
- Encrypted database storage
- Secure key management

#### PC Control Security
- Comprehensive audit logging
- Rate limiting to prevent abuse
- Protected system processes
- Dangerous command blacklist
- Path sandboxing for file operations

### 🎭 Personality System
Lily adapts to your needs with different personalities:

| Personality | Emoji | Description |
|-------------|-------|-------------|
| Lily (Default) | 🌸 | Smart, caring AI girlfriend with sarcasm and warmth |
| Friendly | 🥰 | Warm, supportive best friend |
| Professional | 💼 | Executive assistant mode |
| Playful | 🎉 | Fun, energetic companion |
| Commander | ⚡ | Direct, efficient task-focused mode |
| Scholar | 📚 | Knowledgeable, educational mode |
| Sassy | 💅 | Witty, sarcastic friend |
| Creative | 🎨 | Artistic, imaginative mode |
| Zen | 🧘 | Calm, mindful companion |
| Charming | ✨ | Charismatic, engaging personality |
| Companion | 💕 | Deeply caring, supportive partner |
| Mentor | 🎯 | Wise, guiding advisor |

### 🔌 Plugin System (11 Built-in Plugins)
- `/weather` - Real-time weather information
- `/calc` - Advanced calculator
- `/note` - Personal notes system
- `/todo` - Task management
- `/remind` - Smart reminders
- `/timer` - Countdown timers
- `/crypto` - Cryptocurrency prices
- `/news` - Latest tech news
- `/define` - Dictionary definitions
- `/translate` - Language translation
- `/sysinfo` - Detailed system information

### 🔗 MCP (Model Context Protocol) Support
Lily natively supports MCP-style tool calling:
- Structured tool invocation format
- Batch tool execution support
- Real-time data fetching capabilities
- External API integration ready
- Extensible tool architecture

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd lily-bot

# Run the setup wizard
python setup.py

# Edit configuration
nano .env

# Start the bot
python nova_bot.py
```

### Option 2: Manual Installation

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure Environment**
Create a `.env` file with your settings:
```bash
# Required: Get from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Required: Your Telegram user ID (use @userinfobot)
AUTHORIZED_USER_IDS=your_user_id_here

# AI Configuration
OLLAMA_MODEL=qwen2.5-coder:3b
OLLAMA_BASE_URL=http://localhost:11434

# Optional Settings
SQLITE_PATH=nova.sqlite3
NOVA_LOG_FILE=nova.log
ALLOWED_DIR=./files_safe
CONTEXT_MESSAGES=8
OPENWEATHER_API_KEY=your_weather_api_key
```

3. **Install Ollama** (for local AI)
```bash
# Visit https://ollama.ai for installation
# Then pull a model:
ollama pull qwen2.5-coder:3b
```

4. **Run the Bot**
```bash
# Standard mode
python nova_bot.py

# With web dashboard
python run_with_dashboard.py
```

## 📁 Project Structure

```
lily-bot/
├── nova_bot.py           # Main bot application
├── config.py             # Configuration management
├── db.py                 # Database operations
├── personalities.py      # Personality system
├── pc_control.py         # PC control functions
├── skills_module.py      # Advanced skills & tools
├── ollama_client.py      # Ollama AI integration
├── dashboard.py          # Web dashboard
├── encryption.py         # Encryption utilities
├── e2e_encryption.py     # E2E encryption module
├── news_module.py        # News aggregation
├── exchange_module.py    # Currency exchange
├── setup.py              # Automated setup script
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
├── plugins/              # Plugin modules
│   ├── weather.py
│   ├── calc.py
│   ├── notes.py
│   ├── todo.py
│   ├── remind.py
│   ├── timer.py
│   ├── crypto.py
│   ├── news.py
│   ├── define.py
│   ├── translate.py
│   └── sysinfo.py
└── templates/            # Web dashboard templates
    └── dashboard.html
```

## 🛠️ Usage Examples

### Basic Commands
```
/start - Initialize the bot and see welcome message
/personality <name> - Switch personality (e.g., /personality friendly)
/plugins - List all available plugins
```

### Natural Language Examples
Just talk naturally! Lily understands context:
- "What's the weather like?"
- "Take a screenshot"
- "What apps are running?"
- "Remind me to call mom at 5pm"
- "Calculate 15% of 250"
- "Translate 'hello' to French"
- "What's Bitcoin price?"

### Personality Switching
```
/personality lily        # Default caring AI girlfriend
/personality friendly    # Warm best friend mode
/personality professional # Business assistant
/personality playful     # Fun, energetic mode
/personality sassy       # Witty, sarcastic mode
```

## 🔐 Security Best Practices

1. **Protect Your Token**: Never share your `TELEGRAM_BOT_TOKEN`
2. **Authorize Users**: Only trusted user IDs should be in `AUTHORIZED_USER_IDS`
3. **Secure Keys**: Never share `.e2e_key_*` files
4. **Review Logs**: Check `nova.log` for unusual activity
5. **Safe Directory**: Keep file operations within `ALLOWED_DIR`

## 📊 System Requirements

- **Python**: 3.9 or higher
- **Ollama**: For local AI inference (optional but recommended)
- **FFmpeg**: For audio processing
- **Storage**: ~2GB for models and database
- **RAM**: 4GB minimum, 8GB recommended

## 🎯 Roadmap

- [ ] Multi-user support with permissions
- [ ] Voice chat integration
- [ ] Advanced scheduling features
- [ ] Custom plugin marketplace
- [ ] Mobile app companion
- [ ] Enhanced MCP server integration

## 📝 License

This project is provided as-is for personal use. Please review PRIVACY_NOTICE.txt for privacy details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) for local AI inference
- [python-telegram-bot](https://python-telegram-bot.org/) for Telegram integration
- [OpenAI Whisper](https://openai.com/research/whisper) for voice transcription
- All contributors and supporters

## 💬 Support

For issues or questions:
1. Check the logs: `cat nova.log`
2. Verify your `.env` configuration
3. Ensure Ollama is running: `ollama list`
4. Test with: `python test_token.py`

---

**Made with ❤️ by the Lily AI Team**

*"Technology should feel human, not robotic."*
