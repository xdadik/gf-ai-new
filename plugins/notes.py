# pyre-ignore-all-errors
import os  # type: ignore  # pyre-ignore
import json  # type: ignore  # pyre-ignore
from telegram import Update  # type: ignore  # pyre-ignore
from telegram.ext import CommandHandler, ContextTypes  # type: ignore  # pyre-ignore

PLUGIN_DESCRIPTION = "Save and retrieve personal notes. Commands: /note add <name> <text>, /note get <name>, /note list, /note delete <name>"
NOTES_FILE = "plugins_data_notes.json"

def load_notes():
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_notes(notes):
    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(notes, f, indent=4)

async def note_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles note operations."""
    user_id = str(update.effective_user.id)
    args = context.args
    
    if not args:
        await update.message.reply_text("Usage:\n/note add <name> <text>\n/note get <name>\n/note list\n/note delete <name>")
        return

    action = args[0].lower()
    notes = load_notes()
    
    if user_id not in notes:
        notes[user_id] = {}

    if action == "add" and len(args) >= 3:
        name = args[1]
        text = " ".join(args[2:])  # type: ignore  # pyre-ignore
        notes[user_id][name] = text
        save_notes(notes)
        await update.message.reply_text(f"✅ Note '{name}' saved.")
        
    elif action == "get" and len(args) == 2:
        name = args[1]
        if name in notes[user_id]:  # type: ignore  # pyre-ignore
            await update.message.reply_text(f"📝 **{name}**\n\n{notes[user_id][name]}", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"Note '{name}' not found.")
            
    elif action == "list":
        user_notes = list(notes[user_id].keys())
        if user_notes:
            msg = "📋 **Your Notes:**\n" + "\n".join([f"- {n}" for n in user_notes])  # type: ignore  # pyre-ignore
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text("You don't have any notes.")
            
    elif action == "delete" and len(args) == 2:
        name = args[1]
        if name in notes[user_id]:  # type: ignore  # pyre-ignore
            del notes[user_id][name]
            save_notes(notes)
            await update.message.reply_text(f"🗑️ Note '{name}' deleted.")
        else:
            await update.message.reply_text(f"Note '{name}' not found.")
    else:
        await update.message.reply_text("Invalid note command format.")

def setup():
    return [CommandHandler("note", note_command)]
