# pyre-ignore-all-errors
import os  # type: ignore  # pyre-ignore
import json  # type: ignore  # pyre-ignore
from telegram import Update  # type: ignore  # pyre-ignore
from telegram.ext import CommandHandler, ContextTypes  # type: ignore  # pyre-ignore

PLUGIN_DESCRIPTION = "Todo list manager. Commands: /todo add <task>, /todo list, /todo done <id>, /todo delete <id>"
TODO_FILE = "plugins_data_todos.json"

def load_todos():
    if os.path.exists(TODO_FILE):
        try:
            with open(TODO_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_todos(todos):
    with open(TODO_FILE, 'w', encoding='utf-8') as f:
        json.dump(todos, f, indent=4)

async def todo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "📋 **Todo Commands:**\n"
            "/todo add <task> - Add a new task\n"
            "/todo list - Show all tasks\n"
            "/todo done <id> - Mark task as done\n"
            "/todo delete <id> - Delete a task"
        )
        return

    action = args[0].lower()
    todos = load_todos()
    
    if user_id not in todos:
        todos[user_id] = {"tasks": [], "counter": 0}  # type: ignore  # pyre-ignore

    if action == "add" and len(args) >= 2:
        task_text = " ".join(args[1:])  # type: ignore  # pyre-ignore
        todos[user_id]["counter"] += 1
        task_id = todos[user_id]["counter"]
        todos[user_id]["tasks"].append({
            "id": task_id,
            "text": task_text,
            "done": False,
            "created": str(update.message.date)
        })
        save_todos(todos)
        await update.message.reply_text(f"✅ Task added: \"{task_text}\" (ID: {task_id})")
        
    elif action == "list":
        user_tasks = todos[user_id]["tasks"]
        if not user_tasks:
            await update.message.reply_text("📋 You have no tasks!")
            return
        
        active = [t for t in user_tasks if not t["done"]]
        completed = [t for t in user_tasks if t["done"]]
        
        msg = "📋 **Your Tasks:**\n\n"
        if active:
            msg += "🟡 **Active:**\n"
            for t in active:
                msg += f"  [{t['id']}] ☐ {t['text']}\n"
        
        if completed:
            msg += "\n🟢 **Completed:**\n"
            for t in completed:
                msg += f"  [{t['id']}] ☑ {t['text']}\n"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
            
    elif action == "done" and len(args) == 2:
        try:
            task_id = int(args[1])
            task_found = False
            for t in todos[user_id]["tasks"]:  # type: ignore  # pyre-ignore
                if t["id"] == task_id:  # type: ignore  # pyre-ignore
                    t["done"] = True
                    task_found = True
                    break
            if task_found:
                save_todos(todos)
                await update.message.reply_text(f"☑️ Task {task_id} marked as done!")
            else:
                await update.message.reply_text(f"Task {task_id} not found.")
        except ValueError:
            await update.message.reply_text("Invalid task ID.")
            
    elif action == "delete" and len(args) == 2:
        try:
            task_id = int(args[1])
            original_len = len(todos[user_id]["tasks"])
            todos[user_id]["tasks"] = [t for t in todos[user_id]["tasks"] if t["id"] != task_id]
            if len(todos[user_id]["tasks"]) < original_len:  # type: ignore  # pyre-ignore
                save_todos(todos)
                await update.message.reply_text(f"🗑️ Task {task_id} deleted.")
            else:
                await update.message.reply_text(f"Task {task_id} not found.")
        except ValueError:
            await update.message.reply_text("Invalid task ID.")
    else:
        await update.message.reply_text("Invalid command format.")

def setup():
    return [CommandHandler("todo", todo_command)]
