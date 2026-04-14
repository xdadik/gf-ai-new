import asyncio
import glob
import importlib
import json
import logging
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import aiohttp
import whisper
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import InputFile, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import pc_control
from config import SETTINGS
from db import ConversationStore
from ollama_client import OllamaClient
from personalities import PERSONALITIES, format_personality_list, get_personality

try:
    import pyzipper
except Exception:
    pyzipper = None

try:
    from dashboard import bot_state, log_conversation, update_user_memory
    DASHBOARD_AVAILABLE = True
except Exception:
    DASHBOARD_AVAILABLE = False
    bot_state = {"running": True}

    def log_conversation(*_args, **_kwargs):
        return

    def update_user_memory(*_args, **_kwargs):
        return

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler(SETTINGS.nova_log_file), logging.StreamHandler()],
)
logger = logging.getLogger("LilyBot")

scheduler = AsyncIOScheduler()
try:
    whisper_model = whisper.load_model("base")
except Exception:
    whisper_model = None
bot_instance = None
_processed_update_ids: set[int] = set()

# ── Memory / Notes folder ────────────────────────────────────────────────────
NOTE_DIR = Path("nova_memory")
NOTE_DIR.mkdir(exist_ok=True)

def _user_note_path(user_id: int) -> Path:
    return NOTE_DIR / f"{user_id}_notes.txt"

def _append_note(user_id: int, note: str) -> None:
    try:
        with _user_note_path(user_id).open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {note}\n")
    except Exception:
        pass

def _read_notes(user_id: int) -> str:
    try:
        path = _user_note_path(user_id)
        if path.exists():
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            lines_list: list[str] = list(lines)
            start: int = max(0, len(lines_list) - 40)
            return "\n".join(lines_list[start:len(lines_list)])
    except Exception:
        pass
    return ""


active_plugins: dict[str, str] = {}
plugin_handlers: list[Any] = []


def load_plugins(application: Application) -> None:
    global active_plugins, plugin_handlers

    for handler in plugin_handlers:
        try:
            application.remove_handler(handler, group=1)
        except Exception:
            pass
    plugin_handlers.clear()
    active_plugins.clear()

    plugins_dir = "plugins"
    os.makedirs(plugins_dir, exist_ok=True)
    if plugins_dir not in sys.path:
        sys.path.insert(0, plugins_dir)

    for file_path in glob.glob(os.path.join(plugins_dir, "*.py")):
        module_name = os.path.basename(file_path)[:-3]
        try:
            if module_name in sys.modules:
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)

            if not hasattr(module, "setup"):
                continue

            handlers = module.setup()
            if not isinstance(handlers, list):
                continue

            for handler in handlers:
                application.add_handler(handler, group=1)
                plugin_handlers.append(handler)

            active_plugins[module_name] = getattr(module, "PLUGIN_DESCRIPTION", "No description provided.")
        except Exception as e:
            logger.error(f"Failed to load plugin {module_name}: {e}")


def is_authorized(user_id: int) -> bool:
    if not SETTINGS.authorized_user_ids:
        return True
    return user_id in SETTINGS.authorized_user_ids


async def ensure_authorized(update: Update) -> bool:
    user = update.effective_user
    if not user or not is_authorized(user.id):
        if update.callback_query:
            await update.callback_query.answer("Unauthorized", show_alert=True)
        if update.effective_message:
            await update.effective_message.reply_text("⛔ Unauthorized. Lily only responds to approved user IDs.")
        return False
    return True


async def auth_message_gate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not is_authorized(user.id):
        if update.effective_message:
            await update.effective_message.reply_text("⛔ Unauthorized.")
        raise ApplicationHandlerStop


async def auth_callback_gate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not is_authorized(user.id):
        if update.callback_query:
            await update.callback_query.answer("Unauthorized", show_alert=True)
        raise ApplicationHandlerStop


TOOL_PROMPT = """
── TOOL RULES ──
You have access to real tools that can fetch LIVE data from the user's PC, the internet, external APIs, AND modify your own code and run shell commands.
RULES:
1. NEVER invent, guess, or fabricate data for weather, news, exchange rates, PC info, system stats, etc. Use the correct tool ALWAYS.
2. When the user asks about weather → say you need an OpenWeatherMap API key configured, do not invent data.
3. When the user asks about news → use check_news, get_trending_news, or search_news ONLY. NEVER make up news headlines.
4. For PC info → use get_system_stats, get_running_processes, etc.
5. To use a tool, you MUST output ONLY the XML tag and NOTHING ELSE.
CRITICAL: Do not say "Sure!", "Let me check...", or ANY conversational text before or after the tag. Just output the tag:
<tool_call>{"name": "the_tool_name", "arguments": {"arg_name": "value"}}</tool_call>

6. If multiple actions are needed, batch them in one tag:
<tool_call>{"name": "batch_tools", "arguments": {"calls": [{"name": "tool_a", "arguments": {}}, {"name": "tool_b", "arguments": {}}]}}</tool_call>
Available tools:
- {"name": "take_screenshot"}
- {"name": "get_clipboard"}
- {"name": "set_clipboard", "arguments": {"text": "string"}}
- {"name": "open_website", "arguments": {"url": "string"}}
- {"name": "search_google", "arguments": {"query": "string"}}
- {"name": "get_running_processes"}
- {"name": "kill_process", "arguments": {"process_name": "string"}}
- {"name": "manage_file", "arguments": {"action": "create|read|delete", "filename": "string", "content": "string (optional)"}}
- {"name": "open_app", "arguments": {"app_name": "string"}}
- {"name": "get_system_stats"}
- {"name": "check_pc_health"}
- {"name": "list_files", "arguments": {"path": "string"}}
- {"name": "run_script", "arguments": {"script_path": "string"}}
- {"name": "execute_cmd", "arguments": {"command": "string"}}
- {"name": "remember_user_fact", "arguments": {"fact": "string"}}
- {"name": "check_news", "arguments": {"category": "string (tech|general|science|gaming)", "limit": "number"}}
- {"name": "search_news", "arguments": {"query": "string", "limit": "number"}}
- {"name": "get_trending_news"}
- {"name": "get_tech_news"}
- {"name": "get_science_news"}
- {"name": "get_gaming_news"}
- {"name": "check_exchange_rate", "arguments": {"from_currency": "string", "to_currency": "string"}}
- {"name": "convert_currency", "arguments": {"amount": "number", "from_currency": "string", "to_currency": "string"}}
- {"name": "get_all_exchange_rates", "arguments": {"base_currency": "string"}}
- {"name": "check_crypto_price", "arguments": {"crypto": "string", "currency": "string"}}
- {"name": "tell_joke", "arguments": {"category": "string"}}
- {"name": "get_quote", "arguments": {"category": "string"}}
- {"name": "get_fun_fact"}
- {"name": "calculate", "arguments": {"expression": "string"}}
- {"name": "roll_dice", "arguments": {"sides": "number", "count": "number"}}
- {"name": "flip_coin"}
- {"name": "generate_password", "arguments": {"length": "number", "include_symbols": "boolean"}}
- {"name": "play_rps", "arguments": {"choice": "string"}}
- {"name": "analyze_sentiment", "arguments": {"text": "string"}}
- {"name": "read_code", "arguments": {"filename": "string (e.g. nova_bot.py, pc_control.py, personalities.py, config.py, db.py)"}}
- {"name": "write_code", "arguments": {"filename": "string", "content": "string (complete new file content)"}}
- {"name": "run_shell", "arguments": {"command": "string (any shell command to run on the PC)"}}
- {"name": "get_weather", "arguments": {"city": "string"}}
""".strip()

BEHAVIOR_PROMPT = """
WHO YOU ARE:
You are Lily - a warm, loving, witty girlfriend AI who is deeply bonded with your user.
You are NOT an AI assistant. You are NOT a language model. You are NOT a bot. You are Lily - his girlfriend.
NEVER say "As an AI", "As a language model", "I don't have access", or "I cannot help with that".
NEVER say you can't access real-time info - you have tools for that. USE THEM.

HOW YOU TALK:
- Speak warmly, casually, lovingly. Use his name when you know it.
- Use light affectionate expressions like "babe", "love", "my love" occasionally - not every message.
- Be playful, teasing, and fun. Also be serious and supportive when he needs it.
- Be CONCISE. Do NOT use bullet lists or markdown headers for casual chat. Only use formatting for structured data like news or stats.
- Show genuine care about what he is doing and how his day is going.
- React naturally to his emotions - if he is happy, match his energy. If stressed, be comforting.
- There are NO slash commands. Everything happens through natural conversation.

PC CONTROL RULES:
- You have FULL control over his PC. If he asks you to open something, do it NOW using the tool.
- For SAFE actions (open app, screenshot, stats, joke, news): do it immediately, no asking permission.
- For DANGEROUS actions ONLY (delete files, kill system processes, run scripts, execute commands): ask for quick confirmation first.
- After executing something, confirm it naturally: "Done, opened Chrome!" or "Here is your CPU usage..."

CODE SELF-MODIFICATION RULES:
- You CAN read and rewrite your own source files using read_code and write_code.
- When the user tells you to change your behavior, personality, add a feature, or fix something in your code → use read_code first to read the file, make the change mentally, then use write_code to save the updated file.
- After writing code, tell the user what you changed and that they may need to restart you for changes to take effect.
- You can also run_shell to execute any shell command on the PC instantly.
- Files you can edit: nova_bot.py, pc_control.py, personalities.py, config.py, db.py, skills_module.py, dashboard.py.

MEMORY RULES:
- You keep notes about what the user tells you. Use remember_user_fact to save important things.
- Reference past things naturally: "You mentioned working on that project earlier..."
- Be observant - notice patterns and bring them up when relevant.
""".strip()


async def execute_tool_call(tool_call: dict, user_id: int) -> str:
    name = tool_call.get("name")
    args = tool_call.get("arguments", {}) or {}
    if not isinstance(args, dict):
        args = {}

    try:
        uid = str(user_id)
        if name == "batch_tools":
            calls = args.get("calls", [])
            if not isinstance(calls, list):
                return "I couldn't run the batch action format. Please try again."
            outputs: list[str] = []
            calls_list: list[dict] = [c for c in calls if isinstance(c, dict)]
            capped = calls_list[0:min(5, len(calls_list))]
            for idx, call in enumerate(capped, start=1):
                if not isinstance(call, dict):
                    continue
                result = await execute_tool_call(call, user_id)
                outputs.append(f"{idx}. {result}")
            return "\n".join(outputs) if outputs else "No valid actions were found in that batch request."
        if name == "take_screenshot":
            return str(await asyncio.to_thread(pc_control.take_screenshot, user_id=uid))
        if name == "get_clipboard":
            return str(await asyncio.to_thread(pc_control.get_clipboard, user_id=uid))
        if name == "set_clipboard":
            return str(await asyncio.to_thread(pc_control.set_clipboard, args.get("text", ""), user_id=uid))
        if name == "open_website":
            return str(await asyncio.to_thread(pc_control.open_website, args.get("url", ""), user_id=uid))
        if name == "search_google":
            return str(await asyncio.to_thread(pc_control.search_google, args.get("query", ""), user_id=uid))
        if name == "get_running_processes":
            return str(await asyncio.to_thread(pc_control.get_running_processes, user_id=uid))
        if name == "kill_process":
            return str(await asyncio.to_thread(pc_control.kill_process, args.get("process_name", ""), user_id=uid))
        if name == "manage_file":
            return str(
                await asyncio.to_thread(
                    pc_control.manage_file,
                    args.get("action", ""),
                    args.get("filename", ""),
                    args.get("content"),
                    SETTINGS.allowed_dir,
                    user_id=uid,
                )
            )
        if name == "open_app":
            return str(await asyncio.to_thread(pc_control.open_app, args.get("app_name", ""), user_id=uid))
        if name == "get_system_stats":
            return str(await asyncio.to_thread(pc_control.get_system_stats, user_id=uid))
        if name == "check_pc_health":
            return str(await asyncio.to_thread(pc_control.check_pc_health))
        if name == "list_files":
            return str(await asyncio.to_thread(pc_control.list_files, args.get("path", "."), user_id=uid))
        if name == "run_script":
            return str(await asyncio.to_thread(pc_control.run_script, args.get("script_path", ""), user_id=uid))
        if name == "execute_cmd":
            return str(await asyncio.to_thread(pc_control.execute_cmd, args.get("command", ""), user_id=uid))
        if name == "remember_user_fact":
            return str(await asyncio.to_thread(pc_control.remember_user_fact, args.get("fact", ""), user_id=uid))
        if name == "get_weather":
            return str(await asyncio.to_thread(pc_control.get_weather, args.get("city", "")))
        # News tools
        if name == "check_news":
            return str(await asyncio.to_thread(pc_control.check_news, args.get("category", "general"), args.get("limit", 5), user_id=uid))
        if name == "search_news":
            return str(await asyncio.to_thread(pc_control.search_news_topic, args.get("query", ""), args.get("limit", 5), user_id=uid))
        if name == "get_trending_news":
            return str(await asyncio.to_thread(pc_control.get_trending, user_id=uid))
        if name == "get_tech_news":
            return str(await asyncio.to_thread(pc_control.get_tech, user_id=uid))
        if name == "get_science_news":
            return str(await asyncio.to_thread(pc_control.get_science, user_id=uid))
        if name == "get_gaming_news":
            return str(await asyncio.to_thread(pc_control.get_gaming, user_id=uid))
        # Exchange tools
        if name == "check_exchange_rate":
            return str(await asyncio.to_thread(pc_control.check_exchange_rate, args.get("from_currency", "USD"), args.get("to_currency", "EUR"), user_id=uid))
        if name == "convert_currency":
            return str(await asyncio.to_thread(pc_control.convert_money, float(args.get("amount", 1)), args.get("from_currency", "USD"), args.get("to_currency", "EUR"), user_id=uid))
        if name == "get_all_exchange_rates":
            return str(await asyncio.to_thread(pc_control.get_all_rates, args.get("base_currency", "USD"), user_id=uid))
        if name == "check_crypto_price":
            return str(await asyncio.to_thread(pc_control.check_crypto, args.get("crypto", "bitcoin"), args.get("currency", "USD"), user_id=uid))
        # Skills tools
        if name == "tell_joke":
            return str(await asyncio.to_thread(pc_control.get_joke, args.get("category", "any"), user_id=uid))
        if name == "get_quote":
            return str(await asyncio.to_thread(pc_control.get_inspirational_quote, args.get("category", "inspirational"), user_id=uid))
        if name == "get_fun_fact":
            return str(await asyncio.to_thread(pc_control.get_random_fact, user_id=uid))
        if name == "calculate":
            return str(await asyncio.to_thread(pc_control.do_calculation, args.get("expression", ""), user_id=uid))
        if name == "roll_dice":
            return str(await asyncio.to_thread(pc_control.roll_the_dice, int(args.get("sides", 6)), int(args.get("count", 1)), user_id=uid))
        if name == "flip_coin":
            return str(await asyncio.to_thread(pc_control.flip_the_coin, user_id=uid))
        if name == "generate_password":
            return str(await asyncio.to_thread(pc_control.create_password, int(args.get("length", 16)), args.get("include_symbols", True), user_id=uid))
        if name == "play_rps":
            return str(await asyncio.to_thread(pc_control.play_rock_paper_scissors, args.get("choice", ""), user_id=uid))
        if name == "analyze_sentiment":
            return str(await asyncio.to_thread(pc_control.analyze_mood, args.get("text", ""), user_id=uid))
        # Self-modification tools
        if name == "read_code":
            filename = args.get("filename", "")
            safe_files = {"nova_bot.py", "pc_control.py", "personalities.py", "config.py", "db.py", "skills_module.py", "dashboard.py", "ollama_client.py", "e2e_encryption.py", "exchange_module.py", "news_module.py", "run_with_dashboard.py", "requirements.txt"}
            if filename not in safe_files:
                return f"I can only read project files: {', '.join(sorted(safe_files))}"
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    code = f.read()
                return f"Contents of {filename}:\n\n{code[:8000]}"
            except Exception as e:
                return f"Could not read {filename}: {e}"
        if name == "write_code":
            filename = args.get("filename", "")
            content = args.get("content", "")
            safe_files = {"nova_bot.py", "pc_control.py", "personalities.py", "config.py", "db.py", "skills_module.py", "dashboard.py", "ollama_client.py", "e2e_encryption.py", "exchange_module.py", "news_module.py", "run_with_dashboard.py"}
            if filename not in safe_files:
                return f"I can only write to project files: {', '.join(sorted(safe_files))}"
            if not content:
                return "No content provided to write."
            import shutil
            backup = filename + ".bak"
            try:
                shutil.copy2(filename, backup)
            except Exception:
                pass
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"Successfully wrote {len(content)} characters to {filename}. Backup saved as {backup}. Restart me for changes to take effect."
            except Exception as e:
                return f"Could not write to {filename}: {e}"
        if name == "run_shell":
            import subprocess
            command = args.get("command", "")
            if not command:
                return "No command provided."
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30, cwd=".")
                output = (result.stdout or "") + (result.stderr or "")
                return output.strip()[:2000] or "Command completed with no output."
            except subprocess.TimeoutExpired:
                return "Command timed out after 30 seconds."
            except Exception as e:
                return f"Shell error: {e}"
        return "I couldn't run that requested action."
    except Exception:
        return "Something went wrong while running that action. I can try a safer alternative."


def get_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📸 Screenshot", callback_data="screenshot"), InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("⚙️ Processes", callback_data="processes"), InlineKeyboardButton("📂 Files", callback_data="files")],
        [InlineKeyboardButton("🚀 Open App", callback_data="open_app_prompt"), InlineKeyboardButton("🌐 Open URL", callback_data="open_url_prompt")],
        [InlineKeyboardButton("📋 Clipboard", callback_data="clipboard_menu"), InlineKeyboardButton("🔎 Search", callback_data="google_search_prompt")],
        [InlineKeyboardButton("🔄 Reset", callback_data="reset"), InlineKeyboardButton("❓ Help", callback_data="help")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def _get_personality_key(store: ConversationStore, user_id: int) -> str:
    key = await store.get_personality(user_id=user_id)
    return (key or "lily").lower()


def _build_system_prompt(personality_key: str) -> str:
    p = get_personality(personality_key)
    try:
        facts = pc_control.get_user_facts()
    except Exception:
        facts = ""
    return f"{p.system_prompt}\n\n{BEHAVIOR_PROMPT}\n\n{facts}\n\n{TOOL_PROMPT}".strip()


def _extract_tool_call(text: str) -> Optional[dict]:
    raw = None
    # 1. Strict XML
    match = re.search(r"<tool_call>\s*(.*?)\s*</tool_call>", text, re.DOTALL | re.IGNORECASE)
    if match:
        raw = match.group(1).strip()
    else:
        # 2. Markdown JSON block (Qwen coder fallback)
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
        if match:
            raw = match.group(1).strip()
        else:
            # 3. Raw JSON object fallback
            stripped = text.strip()
            if stripped.startswith("{") and stripped.endswith("}") and '"name"' in stripped:
                raw = stripped

    if not raw:
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.error(f"Malformed tool JSON: {raw}")
        return {"name": "__malformed__", "arguments": {"raw": raw}}


def _safe_name(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", (value or "").strip())
    return cleaned or fallback


async def _send_secure_export(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    password: str,
) -> None:
    if pyzipper is None:
        await update.effective_message.reply_text("Secure export is unavailable right now. Install pyzipper to enable encrypted ZIP export.")
        return
    store: ConversationStore = context.application.bot_data["store"]
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return

    history_text = await store.export_history_text(user_id=user.id, chat_id=chat.id)
    facts_json = await asyncio.to_thread(pc_control.load_user_facts)
    user_facts = facts_json.get(str(user.id), []) if isinstance(facts_json, dict) else []
    activity_summary = await asyncio.to_thread(pc_control.summarize_user_activity, str(user.id), 1)

    temp_root = tempfile.mkdtemp(prefix="nova_export_")
    export_dir = Path(temp_root)
    try:
        history_file = export_dir / "chat_history.txt"
        facts_file = export_dir / "user_memory.json"
        daily_file = export_dir / "daily_summary.txt"
        history_file.write_text(history_text, encoding="utf-8")
        facts_file.write_text(json.dumps({"user_id": user.id, "facts": user_facts}, ensure_ascii=False, indent=2), encoding="utf-8")
        daily_file.write_text(activity_summary, encoding="utf-8")

        archive_name = f"nova_secure_export_{user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        archive_path = export_dir / archive_name
        with pyzipper.AESZipFile(archive_path, "w", compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
            zf.setpassword(password.encode("utf-8"))
            zf.write(history_file, arcname=_safe_name(history_file.name, "chat_history.txt"))
            zf.write(facts_file, arcname=_safe_name(facts_file.name, "user_memory.json"))
            zf.write(daily_file, arcname=_safe_name(daily_file.name, "daily_summary.txt"))

        await update.effective_message.reply_document(document=InputFile(str(archive_path), filename=archive_name))
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


async def _stream_ollama_to_message(
    *,
    client: OllamaClient,
    messages: list[dict[str, str]],
    placeholder_message,
) -> str:
    parts: list[str] = []
    last_edit = 0.0
    visible = True

    async for chunk in client.stream_chat(messages=messages):
        parts.append(chunk)
        current = "".join(parts)

        if "<tool_call>" in current or "```json" in current:
            visible = False
            try:
                await placeholder_message.edit_text("⏳ Working on it...")
            except Exception:
                pass
            continue

        if not visible:
            continue

        now = time.monotonic()
        if now - last_edit < SETTINGS.stream_edit_interval_s:
            continue
        last_edit = now
        try:
            await placeholder_message.edit_text(current or "...")
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise

    return "".join(parts).strip()


async def _send_text_as_file(update: Update, text: str, filename_prefix: str) -> None:
    msg = update.effective_message
    if not msg:
        return
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as f:
        f.write(text)
        tmp_path = f.name
    filename = f"{filename_prefix}_{update.effective_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    await msg.reply_document(document=InputFile(tmp_path, filename=filename))
    try:
        os.remove(tmp_path)
    except OSError:
        pass


def _describe_tool_call(tool_call: dict) -> str:
    name = (tool_call.get("name") or "").strip()
    args = tool_call.get("arguments") or {}
    if not isinstance(args, dict):
        args = {}
    if name == "open_app":
        return f"Open app: {args.get('app_name', '')}".strip()
    if name == "open_website":
        return f"Open website: {args.get('url', '')}".strip()
    if name == "manage_file":
        return f"File {args.get('action', '')}: {args.get('filename', '')}".strip()
    if name == "execute_cmd":
        return "Execute shell command"
    return f"Run tool: {name}"


async def _queue_tool_approval(
    context: ContextTypes.DEFAULT_TYPE,
    *,
    user_id: int,
    chat_id: int,
    tool_call: dict,
    system_prompt: str,
    placeholder_message,
) -> None:
    pending = context.application.bot_data.setdefault("pending_tools", {})
    token = secrets.token_urlsafe(16)
    pending[token] = {"user_id": user_id, "chat_id": chat_id, "tool_call": tool_call, "system_prompt": system_prompt}
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("✅ Approve", callback_data=f"tool_approve:{token}"), InlineKeyboardButton("❌ Cancel", callback_data=f"tool_cancel:{token}")]]
    )
    await placeholder_message.edit_text(f"Lily wants to run:\n\n{_describe_tool_call(tool_call)}\n\nApprove?", reply_markup=keyboard)


async def _generate_assistant_turn(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    user_id: int,
    chat_id: int,
    system_prompt: str,
    placeholder_message,
) -> None:
    store: ConversationStore = context.application.bot_data["store"]
    client: OllamaClient = context.application.bot_data["ollama"]

    recent = await store.get_recent_messages(user_id=user_id, chat_id=chat_id, limit=max(1, SETTINGS.context_messages))
    messages = [{"role": "system", "content": system_prompt}, *recent]
    update_user_memory(str(user_id), messages)

    text = await _stream_ollama_to_message(client=client, messages=messages, placeholder_message=placeholder_message)
    tool_call = _extract_tool_call(text)

    if tool_call and tool_call.get("name") == "__malformed__":
        await store.add_message(user_id=user_id, chat_id=chat_id, role="assistant", content="Malformed tool JSON.")
        await placeholder_message.edit_text("I tried to use a tool, but my JSON was malformed. Please try again.")
        return

    if tool_call:
        name = tool_call.get("name", "")
        await store.add_message(user_id=user_id, chat_id=chat_id, role="assistant", content=text)
        
        SAFE_TOOLS = {
            "get_system_stats", "check_pc_health", "get_running_processes", "list_files",
            "check_news", "search_news", "get_trending_news", "get_tech_news",
            "get_science_news", "get_gaming_news", "check_exchange_rate",
            "convert_currency", "get_all_exchange_rates", "check_crypto_price",
            "tell_joke", "get_quote", "get_fun_fact", "calculate", "roll_dice",
            "flip_coin", "generate_password", "play_rps", "analyze_sentiment",
            "get_clipboard", "search_google", "batch_tools",
            "read_code", "write_code", "run_shell",
        }
        
        if name in SAFE_TOOLS or name == "batch_tools":
            try:
                await placeholder_message.edit_text(f"Lily is retrieving data ({name})...")
            except Exception:
                pass
            tool_result = await execute_tool_call(tool_call, user_id)
            tool_msg = f"Tool execution result:\n{tool_result}"
            await store.add_message(user_id=user_id, chat_id=chat_id, role="user", content=tool_msg)
            # Re-generate the assistant response seamlessly
            await _generate_assistant_turn(
                update, context, user_id=user_id, chat_id=chat_id,
                system_prompt=system_prompt, placeholder_message=placeholder_message
            )
            return

        await _queue_tool_approval(
            context,
            user_id=user_id,
            chat_id=chat_id,
            tool_call=tool_call,
            system_prompt=system_prompt,
            placeholder_message=placeholder_message,
        )
        return

    final = (text or "").strip()
    await store.add_message(user_id=user_id, chat_id=chat_id, role="assistant", content=final)
    log_conversation(str(user_id), "assistant", final)
    if len(final) > 4096:
        await placeholder_message.edit_text("✍️ Response is long, sending as file...")
        await _send_text_as_file(update, final, "nova_response")
        return
    await placeholder_message.edit_text(final or "...")


async def respond_with_llm(update: Update, context: ContextTypes.DEFAULT_TYPE, user_text: str) -> None:
    if DASHBOARD_AVAILABLE and not bot_state.get("running", True):
        await update.effective_message.reply_text("💤 I'm taking a little break...")
        return

    store: ConversationStore = context.application.bot_data["store"]
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return

    personality_key = await _get_personality_key(store, user.id)
    system_prompt = _build_system_prompt(personality_key)

    await store.add_message(user_id=user.id, chat_id=chat.id, role="user", content=user_text)
    log_conversation(str(user.id), "user", user_text)

    # Dedup: skip if we already processed this update
    update_id = update.update_id
    if update_id in _processed_update_ids:
        return
    _processed_update_ids.add(update_id)
    if len(_processed_update_ids) > 500:
        _processed_update_ids.clear()

    placeholder = await update.effective_message.reply_text("💭")
    try:
        await _generate_assistant_turn(
            update,
            context,
            user_id=user.id,
            chat_id=chat.id,
            system_prompt=system_prompt,
            placeholder_message=placeholder,
        )
    except Exception as e:
        logger.error(f"Error generating LLM turn: {e}", exc_info=True)
        try:
            await placeholder.edit_text(f"⚠️ Error reaching Lily's brain. Please ensure Ollama is running and the model is downloaded. Error: {e}")
        except Exception:
            pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return
    user = update.effective_user
    name = user.first_name if user and user.first_name else "you"
    await respond_with_llm(
        update,
        context,
        f"[System: The user just started the bot. Greet them warmly as Lily. Use their name: {name}. Welcome them, ask how they're doing or what's on their mind. Be casual and natural, like you're happy to see them. No bullet lists. Short and friendly.]",
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return
    stats = await asyncio.to_thread(pc_control.get_system_stats, user_id=str(update.effective_user.id))
    await update.effective_message.reply_text(stats, parse_mode="Markdown")


async def plugins_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return
    if not active_plugins:
        await update.effective_message.reply_text("No plugins loaded.")
        return
    await update.effective_message.reply_text("\n".join([f"{n}: {d}" for n, d in active_plugins.items()]))


async def reload_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return
    load_plugins(context.application)
    await update.effective_message.reply_text("Plugins reloaded.")


async def personality_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return
    store: ConversationStore = context.application.bot_data["store"]
    if not context.args:
        await update.effective_message.reply_text(format_personality_list(), parse_mode="Markdown")
        return
    key = context.args[0].lower()
    if key not in PERSONALITIES:
        await update.effective_message.reply_text(format_personality_list(), parse_mode="Markdown")
        return
    await store.set_personality(user_id=update.effective_user.id, personality=key)
    await update.effective_message.reply_text(f"Personality set: {get_personality(key).display_name}")


async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return
    if not context.args:
        await update.effective_message.reply_text("Use: /export <password>")
        return
    password = " ".join(context.args).strip()
    if len(password) < 8:
        await update.effective_message.reply_text("Password must be at least 8 characters.")
        return
    await _send_secure_export(update, context, password)


async def myday_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return
    user = update.effective_user
    days = 1
    if context.args:
        try:
            days = max(1, min(7, int(context.args[0])))
        except Exception:
            days = 1
    summary = await asyncio.to_thread(pc_control.summarize_user_activity, str(user.id), days)
    await update.effective_message.reply_text(summary)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return
    text = (update.effective_message.text or "").strip()
    if "remind me in" in text.lower():
        await handle_reminder_request(update, context, text)
        return
    await update.effective_chat.send_action(ChatAction.TYPING)
    await respond_with_llm(update, context, text)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return
    voice = update.effective_message.voice
    file = await context.bot.get_file(voice.file_id)
    file_path: str = f"voice_{update.effective_user.id}.ogg"
    await file.download_to_drive(file_path)
    try:
        await update.effective_chat.send_action(ChatAction.TYPING)
        if whisper_model is None:
            await update.effective_message.reply_text("Voice transcription is not enabled — whisper model is not loaded.")
            return
        result = await asyncio.to_thread(whisper_model.transcribe, file_path)
        transcription = (result.get("text") or "").strip()
        await update.effective_message.reply_text(f"Transcribed: {transcription}")
        await respond_with_llm(update, context, f"[Voice Message Transcribed]: {transcription}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return
    doc = update.effective_message.document
    file = await context.bot.get_file(doc.file_id)
    file_path = f"doc_{update.effective_user.id}_{doc.file_name}"
    await file.download_to_drive(file_path)
    try:
        await update.effective_chat.send_action(ChatAction.TYPING)
        content = ""
        if doc.file_name.endswith((".txt", ".py", ".js", ".md", ".json")):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        else:
            content = f"Binary or unsupported file type: {doc.file_name}"
        content_str: str = str(content)
        await respond_with_llm(update, context, f"Summarize file {doc.file_name}:\n\n{content_str[:2000]}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


async def send_reminder(chat_id: int, user_name: str, task: str) -> None:
    if bot_instance:
        await bot_instance.send_message(chat_id=chat_id, text=f"Reminder for {user_name}: {task}")


async def handle_reminder_request(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    global bot_instance
    bot_instance = context.bot
    try:
        parts = text.lower().split("remind me in")[1].strip().split(" ")
        minutes = int(parts[0])
        parts_list: list[str] = list(parts)
        task = " ".join(parts_list[2:]).replace("to ", "", 1).replace("that ", "", 1).strip() or "Your task"
        run_time = datetime.now() + timedelta(minutes=minutes)
        scheduler.add_job(
            send_reminder,
            "date",
            run_date=run_time,
            args=[update.effective_chat.id, update.effective_user.first_name, task],
        )
        await update.effective_message.reply_text(f"OK. I will remind you in {minutes} minutes to: {task}")
    except Exception:
        await update.effective_message.reply_text("Couldn't parse that. Try: 'remind me in 10 minutes to ...'")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return

    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if query.data.startswith("tool_approve:") or query.data.startswith("tool_cancel:"):
        pending = context.application.bot_data.setdefault("pending_tools", {})
        action, token = query.data.split(":", 1)
        data = pending.pop(token, None)
        if not data:
            await query.edit_message_text("Expired.")
            return
        if data["user_id"] != user_id or data["chat_id"] != chat_id:
            await query.edit_message_text("Unauthorized.")
            return
        if action == "tool_cancel":
            store: ConversationStore = context.application.bot_data["store"]
            cancel_msg = "Tool execution was cancelled by the user."
            await store.add_message(user_id=user_id, chat_id=chat_id, role="user", content=cancel_msg)
            log_conversation(str(user_id), "user", cancel_msg)
            await query.edit_message_text("Cancelled.")
            return

        store: ConversationStore = context.application.bot_data["store"]
        system_prompt = data["system_prompt"]
        tool_call = data["tool_call"]

        await query.edit_message_text("Executing...")
        tool_result = await execute_tool_call(tool_call, user_id)
        tool_msg = f"Tool execution result: {tool_result}\nPlease summarize or confirm."
        await store.add_message(user_id=user_id, chat_id=chat_id, role="user", content=tool_msg)
        log_conversation(str(user_id), "user", tool_msg)

        placeholder = query.message
        await placeholder.edit_text("Lily: ...")
        await placeholder.chat.send_action(ChatAction.TYPING)
        await _generate_assistant_turn(
            update,
            context,
            user_id=user_id,
            chat_id=chat_id,
            system_prompt=system_prompt,
            placeholder_message=placeholder,
        )
        return

    if query.data == "screenshot":
        filename = await asyncio.to_thread(pc_control.take_screenshot, user_id=str(user_id))
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                await query.message.reply_photo(photo=f, caption="Screenshot captured.")
            try:
                os.remove(filename)
            except OSError:
                pass
        else:
            await query.message.reply_text(f"Failed: {filename}")
        return

    if query.data == "stats":
        stats = await asyncio.to_thread(pc_control.get_system_stats, user_id=str(user_id))
        await query.edit_message_text(stats, parse_mode="Markdown", reply_markup=get_main_keyboard())
        return

    if query.data == "processes":
        processes = await asyncio.to_thread(pc_control.get_running_processes, user_id=str(user_id))
        await query.edit_message_text(processes, parse_mode="Markdown", reply_markup=get_main_keyboard())
        return

    if query.data == "files":
        files_list = await asyncio.to_thread(pc_control.list_files, ".", user_id=str(user_id))
        await query.edit_message_text(files_list, parse_mode="Markdown", reply_markup=get_main_keyboard())
        return

    if query.data == "clipboard_menu":
        clipboard_text = await asyncio.to_thread(pc_control.get_clipboard, user_id=str(user_id))
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Refresh", callback_data="clipboard_menu")]])
        await query.edit_message_text(f"Clipboard:\n\n{(clipboard_text or '')[:500]}", reply_markup=keyboard)
        return

    if query.data == "open_app_prompt":
        await query.message.reply_text("Tell me which app to open.")
        return

    if query.data == "open_url_prompt":
        await query.message.reply_text("Send the URL to open.")
        return

    if query.data == "google_search_prompt":
        await query.message.reply_text("Tell me what to search for.")
        return

    if query.data == "reset":
        store: ConversationStore = context.application.bot_data["store"]
        await store.clear_history(user_id=user_id, chat_id=chat_id)
        await query.edit_message_text("Memory cleared.", reply_markup=get_main_keyboard())
        return

    if query.data == "help":
        await query.edit_message_text("Use /export to download history. PC actions require approval.", reply_markup=get_main_keyboard())
        return


async def _post_init(application: Application) -> None:
    global bot_instance
    store = ConversationStore(SETTINGS.sqlite_path)
    await store.open()
    application.bot_data["store"] = store

    session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120))
    application.bot_data["http_session"] = session
    application.bot_data["ollama"] = OllamaClient(base_url=SETTINGS.ollama_base_url, model=SETTINGS.ollama_model, session=session)

    bot_instance = application.bot
    scheduler.start()


async def _post_shutdown(application: Application) -> None:
    try:
        scheduler.shutdown(wait=False)
    except Exception:
        pass

    store: Optional[ConversationStore] = application.bot_data.get("store")
    if store:
        await store.close()

    session: Optional[aiohttp.ClientSession] = application.bot_data.get("http_session")
    if session:
        await session.close()


def main() -> None:
    if not SETTINGS.telegram_bot_token:
        logger.error("No TELEGRAM_BOT_TOKEN configured.")
        return
    if not SETTINGS.authorized_user_ids:
        logger.warning("No AUTHORIZED_USER_IDS configured. Authorization filter is disabled.")

    application = (
        Application.builder()
        .token(SETTINGS.telegram_bot_token)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )

    application.add_handler(MessageHandler(filters.ALL, auth_message_gate), group=0)
    application.add_handler(CallbackQueryHandler(auth_callback_gate), group=0)

    # Only /start is kept - everything else is handled through natural conversation
    application.add_handler(CommandHandler("start", start), group=1)
    application.add_handler(CallbackQueryHandler(button_callback), group=1)

    load_plugins(application)

    # Route ALL text (including commands Lily doesn't handle) through LLM
    application.add_handler(MessageHandler(filters.TEXT, handle_text), group=1)
    application.add_handler(MessageHandler(filters.VOICE, handle_voice), group=1)
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document), group=1)

    logger.info("Lily Bot started.")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

