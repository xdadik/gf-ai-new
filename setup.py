#!/usr/bin/env python3
"""
Lily AI Bot - Interactive Setup Wizard
Run this after cloning to configure everything automatically.
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def print_step(text):
    print(f"→ {text}")

def get_input(prompt, default=None, secure=False):
    """Get user input with optional default value."""
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = prompt + ": "

    try:
        if secure:
            import getpass
            value = getpass.getpass(full_prompt)
        else:
            value = input(full_prompt)

        if not value and default:
            return default
        return value.strip()
    except (EOFError, KeyboardInterrupt):
        print("\n\nSetup cancelled.")
        sys.exit(0)

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required.")
        sys.exit(1)
    print_step(f"Python version: {sys.version.split()[0]} ✓")

def install_dependencies():
    """Install all required Python packages."""
    print_step("Installing Python dependencies...")
    requirements_file = Path(__file__).parent / "requirements.txt"

    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        sys.exit(1)

    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "--upgrade", "pip", "-q"
        ])
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "-r", str(requirements_file), "-q"
        ])
        print_step("Dependencies installed successfully ✓")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def get_telegram_credentials():
    """Get Telegram bot token and user ID from user."""
    print_header("Telegram Configuration")
    print("""
To get your Telegram Bot Token:
1. Open Telegram and search for @BotFather
2. Send /newbot command
3. Follow the instructions to create a bot
4. Copy the API token provided
""")

    while True:
        token = get_input("Enter your Telegram Bot Token", secure=True)
        if token and len(token) > 20:
            break
        print("❌ Invalid token. Please enter a valid Telegram bot token.")

    print("\nTo find your Telegram User ID:")
    print("1. Search for @userinfobot on Telegram")
    print("2. Start the bot and it will show your ID\n")

    while True:
        user_id = get_input("Enter your Telegram User ID")
        if user_id and user_id.isdigit():
            break
        print("❌ Invalid ID. Please enter a numeric Telegram user ID.")

    return token, user_id

def configure_ai_backend():
    """Configure AI backend (Ollama or API)."""
    print_header("AI Backend Configuration")
    print("""
Lily can use different AI backends:
1. Ollama (Local, Free) - Recommended for privacy
2. External API (OpenAI-compatible)
""")
    
    choice = get_input("Choose AI backend (1=Ollama, 2=API)", default="1")
    
    if choice == "1":
        print("\nOllama Configuration:")
        print("If you don't have Ollama installed:")
        print("  - Visit https://ollama.ai")
        print("  - Download and install for your OS")
        print("  - Run: ollama pull qwen2.5-coder:3b\n")
        
        model = get_input("Ollama model name", default="qwen2.5-coder:3b")
        base_url = get_input("Ollama base URL", default="http://localhost:11434")
        
        return {
            "type": "ollama",
            "model": model,
            "base_url": base_url
        }
    else:
        print("\nAPI Configuration:")
        api_key = get_input("Enter your API key", secure=True)
        base_url = get_input("API base URL", default="https://api.openai.com/v1")
        model = get_input("Model name", default="gpt-3.5-turbo")
        
        return {
            "type": "api",
            "api_key": api_key,
            "base_url": base_url,
            "model": model
        }

def configure_pc_control():
    """Configure PC control permissions."""
    print_header("PC Control Permissions")
    print("""
Lily can control your PC for tasks like:
- Opening applications and websites
- Taking screenshots
- Managing files
- Running commands
- System monitoring

⚠️  IMPORTANT: Lily will ask for permission before:
- Deleting files
- Killing processes
- Running shell commands
- Any potentially dangerous action

Safe actions (no permission needed):
- System stats and monitoring
- Taking screenshots
- Reading files
- News, weather, calculations
""")
    
    confirm = get_input("Grant Lily full PC control? (yes/no)", default="yes")
    full_control = confirm.lower() in ["yes", "y", "true"]
    
    allowed_dir = get_input("Restricted directory for file operations", default="./files_safe")
    
    return {
        "full_control": full_control,
        "allowed_dir": allowed_dir
    }

def configure_background_mode():
    """Configure background running."""
    print_header("Background Mode")
    print("""
Do you want Lily to run 24/7 in the background?
- Yes: Lily stays active even after you close the terminal
- No: Lily only runs while the terminal is open
""")
    
    choice = get_input("Enable background mode? (yes/no)", default="yes")
    bg_mode = choice.lower() in ["yes", "y", "true"]
    
    if bg_mode:
        print("\nBackground mode enabled.")
        print("Lily will start automatically and stay running.")
        print("Use 'pkill -f nova_bot.py' to stop her.\n")
    
    return bg_mode

def create_env_file(config):
    """Create .env file with user configuration."""
    env_file = Path(__file__).parent / ".env"
    
    ai_config = config["ai"]
    pc_config = config["pc_control"]
    
    env_content = f"""# Lily AI Bot Configuration
# Generated automatically by setup.py

# Telegram Credentials
TELEGRAM_BOT_TOKEN={config['token']}
AUTHORIZED_USER_IDS={config['user_id']}

# AI Backend Configuration
"""
    
    if ai_config["type"] == "ollama":
        env_content += f"""OLLAMA_MODEL={ai_config['model']}
OLLAMA_BASE_URL={ai_config['base_url']}
"""
    else:
        env_content += f"""OPENAI_API_KEY={ai_config['api_key']}
OPENAI_BASE_URL={ai_config['base_url']}
OPENAI_MODEL={ai_config['model']}
OLLAMA_MODEL={ai_config['model']}
"""
    
    env_content += f"""
# PC Control
ALLOWED_DIR={pc_config['allowed_dir']}
FULL_PC_CONTROL={'true' if pc_config['full_control'] else 'false'}

# Database
SQLITE_PATH=nova.sqlite3

# Logging
NOVA_LOG_FILE=nova.log

# Context Settings
CONTEXT_MESSAGES=8
STREAM_EDIT_INTERVAL_S=0.4

# Optional: Weather API
OPENWEATHER_API_KEY=

# Custom Personalities
CUSTOM_PERSONALITIES_FILE=custom_personalities.json
"""
    
    try:
        env_file.write_text(env_content)
        print_step("Configuration saved to .env ✓")
    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")
        sys.exit(1)

def create_directories():
    """Create necessary directories."""
    dirs = ["files_safe", "nova_memory", "logs"]
    
    for dir_name in dirs:
        dir_path = Path(__file__).parent / dir_name
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            print_step(f"Created directory: {dir_name} ✓")

def check_ollama():
    """Check if Ollama is available."""
    print_step("Checking Ollama installation...")
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/tags"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0 and "models" in result.stdout.decode():
            print("✓ Ollama is running")
            return True
        else:
            print("⚠ Ollama is not running - please start it manually")
            return False
    except Exception:
        print("⚠ Ollama is not installed or not running")
        return False

def show_next_steps(bg_mode):
    """Display next steps for the user."""
    print_header("Setup Complete!")
    print("""
🎉 Lily is ready to use!

""")
    
    if bg_mode:
        print("""
Starting Lily in background mode...
She will run 24/7 and be always available.

To stop her: pkill -f nova_bot.py
To view logs: tail -f nova.log

""")
        log_file = Path(__file__).parent / "nova.log"
        with open(log_file, "a") as f:
            subprocess.Popen(
                [sys.executable, str(Path(__file__).parent / "nova_bot.py")],
                stdout=f,
                stderr=f,
                cwd=str(Path(__file__).parent)
            )
        print("✓ Lily is now running in the background!")
    else:
        print("""
To start Lily:
  python nova_bot.py

Or with dashboard:
  python run_with_dashboard.py

""")
    
    print("""
Features enabled:
✓ Natural conversation (no commands needed)
✓ PC control with safety checks
✓ Memory and context awareness
✓ Multiple personalities
✓ Tool calling (MCP compatible)
✓ File operations
✓ System monitoring
✓ News, weather, calculations
✓ Self-modification capabilities

Enjoy your time with Lily! 🌸
""")

def main():
    print_header("Lily AI Bot - Interactive Setup")
    print("""
Welcome! This setup will configure Lily just for you.
She'll be warm, caring, and helpful - never robotic.
Let's get everything ready!\n
""")
    
    check_python_version()
    create_directories()
    
    install_dependencies()
    
    token, user_id = get_telegram_credentials()
    ai_config = configure_ai_backend()
    pc_config = configure_pc_control()
    bg_mode = configure_background_mode()
    
    config = {
        "token": token,
        "user_id": user_id,
        "ai": ai_config,
        "pc_control": pc_config,
        "bg_mode": bg_mode
    }
    
    create_env_file(config)
    
    if ai_config["type"] == "ollama":
        check_ollama()
    
    show_next_steps(bg_mode)

if __name__ == "__main__":
    main()
