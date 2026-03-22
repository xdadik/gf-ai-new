# pyre-ignore-all-errors
import os  # type: ignore  # pyre-ignore
import json  # type: ignore  # pyre-ignore
from datetime import datetime, timedelta  # type: ignore  # pyre-ignore
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  # type: ignore  # pyre-ignore
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler  # type: ignore  # pyre-ignore

PLUGIN_DESCRIPTION = "Persistent reminders. Commands: /remind add <min> <task>, /remind list, /remind delete <id>"
REMINDERS_FILE = "plugins_data_reminders.json"

def load_reminders():
    if os.path.exists(REMINDERS_FILE):
        try:
            with open(REMINDERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_reminders(reminders):
    with open(REMINDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(reminders, f, indent=4)

async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args
    
    if not args or args[0].lower() == "help":  # type: ignore  # pyre-ignore
        await update.message.reply_text(
            "⏰ **Reminder Commands:**\n\n"
            "/remind add <minutes> <task> - Set a reminder\n"
            "/remind list - View all reminders\n"
            "/remind delete <id> - Cancel a reminder"
        )
        return

    action = args[0].lower()
    reminders = load_reminders()
    
    if user_id not in reminders:
        reminders[user_id] = {"items": [], "counter": 0}  # type: ignore  # pyre-ignore

    if action == "add" and len(args) >= 3:
        try:
            minutes = int(args[1])
            if minutes <= 0 or minutes > 10080:
                await update.message.reply_text("Minutes must be between 1 and 10080.")
                return
            
            task = " ".join(args[2:])  # type: ignore  # pyre-ignore
            reminders[user_id]["counter"] += 1
            reminder_id = reminders[user_id]["counter"]
            
            due_time = datetime.now() + timedelta(minutes=minutes)
            
            reminders[user_id]["items"].append({
                "id": reminder_id,
                "task": task,
                "due_time": due_time.isoformat(),
                "minutes": minutes
            })
            
            save_reminders(reminders)
            
            time_str = f"{minutes} minutes" if minutes < 60 else f"{minutes // 60} hour(s)"
            await update.message.reply_text(f"✅ **Reminder Set!**\n\n📝 {task}\n⏰ In: {time_str}\n🆔 ID: {reminder_id}")
        except ValueError:
            await update.message.reply_text("Invalid minutes.")
            
    elif action == "list":
        user_items = reminders[user_id]["items"]
        if not user_items:
            await update.message.reply_text("⏰ No active reminders.")
            return
        
        msg = "⏰ **Your Reminders:**\n\n"
        keyboard = []
        
        for item in user_items:
            due = datetime.fromisoformat(item["due_time"])
            remaining = due - datetime.now()
            
            if remaining.total_seconds() > 0:
                mins = int(remaining.total_seconds() / 60)
                time_left = f"in {mins}m"
            else:
                time_left = "due now!"
            
            msg += f"[{item['id']}] 📌 {item['task']}\n   ⏰ {time_left}\n\n"
            keyboard.append([InlineKeyboardButton(f"Delete #{item['id']}", callback_data=f"remdel_{item['id']}")])
        
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif action == "delete" and len(args) == 2:
        try:
            rem_id = int(args[1])
            original = len(reminders[user_id]["items"])
            reminders[user_id]["items"] = [r for r in reminders[user_id]["items"] if r["id"] != rem_id]
            
            if len(reminders[user_id]["items"]) < original:  # type: ignore  # pyre-ignore
                save_reminders(reminders)
                await update.message.reply_text(f"🗑️ Reminder #{rem_id} deleted.")
            else:
                await update.message.reply_text(f"Reminder #{rem_id} not found.")
        except ValueError:
            await update.message.reply_text("Invalid ID.")

async def reminder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("remdel_"):
        rem_id = int(query.data.split("_")[1])
        user_id = str(update.effective_user.id)
        
        reminders = load_reminders()
        if user_id in reminders:
            original = len(reminders[user_id]["items"])
            reminders[user_id]["items"] = [r for r in reminders[user_id]["items"] if r["id"] != rem_id]
            
            if len(reminders[user_id]["items"]) < original:  # type: ignore  # pyre-ignore
                save_reminders(reminders)
                await query.edit_message_text(f"🗑️ Reminder #{rem_id} deleted.")

def setup():
    return [CommandHandler("remind", remind_command), CallbackQueryHandler(reminder_callback)]
