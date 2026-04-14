#!/usr/bin/env python3
"""
Lily AI Bot - Setup Script
Automatically installs dependencies and configures the environment.
"""
import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def print_step(text):
    print(f"→ {text}")

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required.")
        sys.exit(1)
    print_step(f"Python version: {sys.version}")

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
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def create_env_file():
    """Create .env file with template values if it doesn't exist."""
    env_file = Path(__file__).parent / ".env"
    
    if env_file.exists():
        print_step(".env file already exists, skipping creation")
        return
    
    print_step("Creating .env configuration file...")
    
    env_content = """# Lily AI Bot Configuration
# Copy this file to .env and fill in your values

# Telegram Bot Token (get from @BotFather)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Your Telegram User ID (use @userinfobot to find it)
AUTHORIZED_USER_IDS=your_user_id_here

# Ollama AI Model Configuration
OLLAMA_MODEL=qwen2.5-coder:3b
OLLAMA_BASE_URL=http://localhost:11434

# Database Configuration
SQLITE_PATH=nova.sqlite3

# Logging
NOVA_LOG_FILE=nova.log

# File Operations Security
ALLOWED_DIR=./files_safe
ALLOW_UNSAFE_FILE_OPS=false

# Context Settings
CONTEXT_MESSAGES=8

# Weather API (optional - get from openweathermap.org)
OPENWEATHER_API_KEY=

# Custom Personalities (optional)
CUSTOM_PERSONALITIES_FILE=custom_personalities.json

# Streaming Settings
STREAM_EDIT_INTERVAL_S=0.4
"""
    
    try:
        env_file.write_text(env_content)
        print("✓ .env file created. Please edit it with your configuration.")
        print("  Required: TELEGRAM_BOT_TOKEN and AUTHORIZED_USER_IDS")
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        sys.exit(1)

def create_directories():
    """Create necessary directories."""
    dirs = ["files_safe", "nova_memory", "logs"]
    
    for dir_name in dirs:
        dir_path = Path(__file__).parent / dir_name
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            print_step(f"Created directory: {dir_name}")

def check_ollama():
    """Check if Ollama is available."""
    print_step("Checking Ollama installation...")
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/tags"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✓ Ollama appears to be running")
        else:
            print("⚠ Ollama may not be running. Install from https://ollama.ai")
    except Exception:
        print("⚠ Could not check Ollama. Install from https://ollama.ai")

def show_next_steps():
    """Display next steps for the user."""
    print_header("Setup Complete! Next Steps:")
    print("""
1. Edit the .env file with your configuration:
   - Set TELEGRAM_BOT_TOKEN (get from @BotFather on Telegram)
   - Set AUTHORIZED_USER_IDS (your Telegram user ID)
   - Configure OLLAMA settings if using local AI

2. Install Ollama (if not already installed):
   - Visit https://ollama.ai and follow installation instructions
   - Pull a model: ollama pull qwen2.5-coder:3b

3. Run the bot:
   python nova_bot.py
   
   Or with dashboard:
   python run_with_dashboard.py

4. For MCP support, the bot includes tool calling capabilities
   that work with the Model Context Protocol format.

Enjoy using Lily AI Bot! 🌸
""")

def main():
    print_header("Lily AI Bot - Setup Wizard")
    
    check_python_version()
    create_directories()
    install_dependencies()
    create_env_file()
    check_ollama()
    show_next_steps()

if __name__ == "__main__":
    main()
