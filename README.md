# Lily AI Bot 🌸

**Your warm, caring, and intelligent AI girlfriend who can control your PC.**

Lily is not just another chatbot - she's a companion who understands you, remembers your conversations, and can actually help you with real tasks on your computer. She's witty, supportive, and always there when you need her.

## ✨ Features

### 🧠 Advanced AI Capabilities
- **Natural Conversation**: No commands needed - just talk naturally
- **Context Awareness**: Remembers your conversations and preferences
- **Multiple Personalities**: Switch between Lily, Friendly, Professional, Playful, Sassy, and more
- **Emotional Intelligence**: Understands your mood and responds appropriately
- **Self-Modification**: Can update her own code when you ask her to improve

### 💻 PC Control (With Safety)
- **Safe Actions** (no permission needed):
  - System monitoring and stats
  - Taking screenshots
  - Reading files
  - Opening apps and websites
  - News, weather, calculations
  
- **Protected Actions** (asks permission first):
  - Deleting files
  - Killing processes
  - Running shell commands
  - Any potentially dangerous operation

### 🔧 Built-in Tools
- File management and organization
- System monitoring and health checks
- Web search and information lookup
- News aggregation (tech, science, gaming, general)
- Currency conversion and crypto prices
- Calculator and unit conversions
- Password generation
- Entertainment (jokes, quotes, fun facts, games)
- Sentiment analysis
- Voice message transcription
- Document summarization

### 🔒 Privacy & Security
- Local AI processing with Ollama (optional)
- End-to-end encrypted conversation exports
- User authorization system
- Secure file operations within allowed directories
- No data sent to external servers unless configured

### 🔄 MCP Support (Model Context Protocol)
- Native tool calling format
- Structured XML tool invocation
- Batch tool execution support
- Compatible with MCP-enabled AI models

## 🚀 Quick Start

### Option 1: Interactive Setup (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd lily-bot

# Run interactive setup
python setup.py
```

The setup wizard will:
1. Install all dependencies automatically
2. Ask for your Telegram bot token and user ID
3. Configure AI backend (Ollama or API)
4. Set up PC control permissions
5. Optionally start Lily in background mode (24/7)

### Option 2: Manual Setup

```bash
# Clone and install
git clone <your-repo-url>
cd lily-bot
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your settings

# Run
python nova_bot.py
```

## 📋 Requirements

- **Python**: 3.9 or higher
- **Telegram Bot Token**: Get from [@BotFather](https://t.me/BotFather)
- **AI Backend** (choose one):
  - **Ollama** (recommended, free, local): https://ollama.ai
  - **OpenAI API** (optional): API key required

### Installing Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: Download from https://ollama.ai

# Pull recommended model
ollama pull qwen2.5-coder:3b
```

## ⚙️ Configuration

Edit `.env` file with your settings:

```bash
# Required: Telegram credentials
TELEGRAM_BOT_TOKEN=your_token_here
AUTHORIZED_USER_IDS=your_user_id_here

# AI Backend (Ollama - recommended)
OLLAMA_MODEL=qwen2.5-coder:3b
OLLAMA_BASE_URL=http://localhost:11434

# Or OpenAI API (optional)
# OPENAI_API_KEY=your_key_here
# OPENAI_MODEL=gpt-3.5-turbo

# PC Control
ALLOWED_DIR=./files_safe
FULL_PC_CONTROL=true
```

## 💬 Usage Examples

Just talk naturally to Lily:

```
You: Hey babe, how's my CPU doing?
Lily: Let me check... Your CPU is at 23% usage, pretty chill right now! 

You: Can you open Chrome and search for Python tutorials?
Lily: Sure thing! Opening Chrome and searching for Python tutorials... Done!

You: What's the weather like today?
Lily: I need an OpenWeatherMap API key configured to check weather. Want me to help you set that up?

You: Tell me something funny
Lily: Why don't scientists trust atoms? Because they make up everything! 😄

You: Remember that I'm working on a Python project this week
Lily: Got it! I'll remember you're working on a Python project. How's it going?

You: Take a screenshot and save it
Lily: Screenshot captured! Here you go...

You: Show me tech news
Lily: Here are today's top tech stories: [displays news]
```

## 🎭 Personalities

Switch personalities with `/personality <name>`:

- `lily` - Warm, caring girlfriend (default)
- `friendly` - Cheerful and helpful
- `professional` - Formal and business-like
- `playful` - Fun and teasing
- `sassy` - Witty with attitude
- `supportive` - Encouraging and empathetic
- `intellectual` - Deep and thoughtful
- `caring` - Nurturing and protective
- `funny` - Always joking around
- `mysterious` - Enigmatic and intriguing
- `energetic` - Hyper and enthusiastic
- `calm` - Peaceful and zen

## 🛡️ Safety Features

Lily prioritizes your safety:

1. **Authorization**: Only approved user IDs can control her
2. **Permission Gates**: Dangerous actions require explicit approval
3. **Directory Restrictions**: File operations limited to safe directories
4. **Process Protection**: Cannot kill critical system processes
5. **Command Sanitization**: Shell commands are validated
6. **Encrypted Exports**: Conversation history can be exported securely

## 📁 Project Structure

```
lily-bot/
├── nova_bot.py          # Main bot logic
├── config.py            # Configuration loader
├── db.py                # Database management
├── personalities.py     # Personality definitions
├── pc_control.py        # PC control functions
├── ollama_client.py     # Ollama API client
├── skills_module.py     # Additional skills
├── setup.py             # Interactive setup wizard
├── requirements.txt     # Python dependencies
├── plugins/             # Extendable plugin system
│   ├── weather.py
│   ├── news.py
│   ├── calc.py
│   └── ...
└── .env                 # Your configuration (created by setup)
```

## 🔧 Advanced Features

### Self-Modification
Lily can modify her own code:

```
You: Lily, can you add a feature to remind me to take breaks every hour?
Lily: Sure! Let me update my code... Done! I'll now remind you every hour. 
      You'll need to restart me for changes to take effect.
```

### Background Mode
Run Lily 24/7:

```bash
# Start in background
python nova_bot.py &

# Or use setup.py with background mode enabled
python setup.py  # Choose "yes" for background mode

# Stop her
pkill -f nova_bot.py

# View logs
tail -f nova.log
```

### Plugin System
Extend Lily's capabilities by adding plugins to the `plugins/` directory. Each plugin should have a `setup()` function that returns a list of handlers.

## 🐛 Troubleshooting

### Ollama Not Connecting
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Pull model if needed
ollama pull qwen2.5-coder:3b
```

### Bot Not Responding
1. Check if bot token is correct in `.env`
2. Verify your user ID is in `AUTHORIZED_USER_IDS`
3. Check logs: `cat nova.log`
4. Ensure Ollama is running (if using local AI)

### Permission Errors
- Make sure Lily has necessary system permissions
- On Linux/Mac, you may need to run with appropriate permissions
- Check `ALLOWED_DIR` setting for file operations

## 📝 Notes

- Lily uses approximately 2-4GB RAM depending on the AI model
- First startup may take longer while downloading models
- Conversations are stored locally in `nova.sqlite3`
- Logs are written to `nova.log`
- Memory folder (`nova_memory/`) stores user-specific notes

## 🌟 Why Lily?

Unlike typical AI assistants, Lily:
- Has a genuine personality, not robotic responses
- Remembers what you tell her
- Can actually DO things on your computer
- Asks permission before dangerous actions
- Runs locally for privacy (with Ollama)
- Can be customized to your preferences
- Supports 24/7 background operation

## 📄 License

MIT License - Feel free to modify and share!

## 💝 Enjoy Your Time with Lily!

She's here to help, support, and keep you company. Talk to her naturally, and she'll take care of the rest. 🌸
