# Lily AI Bot

A powerful Telegram bot with **end-to-end encrypted** PC control capabilities, powered by Ollama AI.

## Features

### Core Features
- **AI-Powered Chat**: Conversational AI using Ollama models
- **Voice Messages**: Transcribe and respond to voice messages using Whisper
- **PC Control**: Full system control via natural language
  - Screenshot capture
  - Clipboard management
  - Process monitoring and control
  - File management
  - Application launching
  - System statistics
  - Google search

### Security Features

#### End-to-End Encryption
- All messages between you and Lily are **encrypted**
- Messages appear as `[E2E]xxxxxxxx` in transit
- Only your bot can decrypt your messages
- Database stores messages encrypted

#### PC Control Security
- **Audit Logging**: All PC operations logged
- **Rate Limiting**: Prevents abuse
- **Process Protection**: System processes cannot be killed
- **Command Blacklist**: Dangerous commands blocked
- **Path Sandboxing**: Files restricted to safe directories

### Personality System
Switch between different AI personalities:
- Lily, Code, Humor, Professional, etc.

### Plugin System (11 plugins)
- `/weather` - Weather info
- `/calc` - Calculator
- `/note` - Notes
- `/todo` - Tasks
- `/remind` - Reminders
- `/timer` - Countdown
- `/crypto` - Crypto prices
- `/news` - Tech news
- `/define` - Dictionary
- `/translate` - Translation
- `/sysinfo` - System info

## Installation

```bash
pip install -r requirements.txt
```

Configure `.env`:
```
TELEGRAM_BOT_TOKEN=your_token
AUTHORIZED_USER_IDS=your_id
OLLAMA_MODEL=qwen2.5-coder:3b
OLLAMA_BASE_URL=http://localhost:11434
```

Run:
```bash
python lily_bot.py
python run_with_dashboard.py  # with web dashboard
```

## Encryption Details

### How It Works
1. Each user gets a unique encryption key stored in `.e2e_key_{user_id}`
2. All messages encrypted before sending via Telegram API
3. Messages stored encrypted in database
4. Only the bot (with your key) can decrypt your messages

### Message Format
```
[Normal message]
[E2E]base64encodedencryptedcontent
```

### Security Layers
| Layer | Protection |
|-------|------------|
| Transit | Telegram API (TLS) + custom E2E |
| Storage | Fernet symmetric encryption |
| PC Ops | HMAC signing, rate limiting |
| Files | Path sandboxing, extension blocks |

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Start bot |
| `/stats` | System stats |
| `/personality <name>` | Change personality |
| `/plugins` | List plugins |
| `/reload` | Reload plugins |

## File Structure

```
gf ai/
├── lily_bot.py          # Main bot with E2E
├── db.py               # Encrypted database
├── e2e_encryption.py   # E2E encryption module
├── encryption.py       # PC control encryption
├── pc_control.py      # Secure PC control
├── plugins/           # 11 plugins
└── dashboard.py        # Web dashboard
```

## Security Notes

- Never share your `.e2e_key_*` files
- Each user ID has a unique encryption key
- Rate limits prevent automated attacks
- Dangerous PC operations are logged and limited
