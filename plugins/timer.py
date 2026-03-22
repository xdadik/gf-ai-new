# pyre-ignore-all-errors
import asyncio  # type: ignore  # pyre-ignore
from telegram import Update  # type: ignore  # pyre-ignore
from telegram.ext import CommandHandler, ContextTypes  # type: ignore  # pyre-ignore

PLUGIN_DESCRIPTION = "Countdown timer using /timer <seconds> [message]"

async def timer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets a simple countdown timer."""
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /timer <seconds> [message]")  # type: ignore  # pyre-ignore
        return
        
    try:
        seconds = int(args[0])
        if seconds <= 0 or seconds > 86400: # Max 24 hours
            await update.message.reply_text("Please provide a valid time between 1 and 86400 seconds.")
            return
            
        message = " ".join(args[1:]) if len(args) > 1 else "Time's up!"  # type: ignore  # pyre-ignore
        
        await update.message.reply_text(f"⏳ Timer set for {seconds} seconds.")
        
        # We use a simple asyncio sleep for this plugin example
        # (For persistence across reboots, APScheduler would be better, but this demonstrates a simple plugin)
        await asyncio.sleep(seconds)
        
        await update.message.reply_text(f"⏰ **BEEP BEEP BEEP!**\n\n{message}", parse_mode="Markdown")
        
    except ValueError:
        await update.message.reply_text("Please provide a valid number of seconds.")

def setup():
    return [CommandHandler("timer", timer_command)]
