# pyre-ignore-all-errors
import psutil  # type: ignore  # pyre-ignore
from datetime import datetime  # type: ignore  # pyre-ignore
from telegram import Update  # type: ignore  # pyre-ignore
from telegram.ext import CommandHandler, ContextTypes  # type: ignore  # pyre-ignore

PLUGIN_DESCRIPTION = "System monitoring. Commands: /sysinfo, /disk, /network"

def format_bytes(bytes_val):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:  # type: ignore  # pyre-ignore
        if bytes_val < 1024:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.2f} PB"

async def sysinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    boot_time = psutil.boot_time()
    uptime = datetime.now() - datetime.fromtimestamp(boot_time)
    
    msg = (
        "🖥️ **System Information**\n\n"
        f"**CPU:**\n"
        f"  Frequency: {psutil.cpu_freq().current:.0f} MHz\n"
        f"  Cores: {psutil.cpu_count()} logical, {psutil.cpu_count(logical=False)} physical\n"
        f"  Usage: {psutil.cpu_percent(interval=1)}%\n\n"
        f"**Memory:**\n"
        f"  Total: {format_bytes(psutil.virtual_memory().total)}\n"
        f"  Available: {format_bytes(psutil.virtual_memory().available)}\n"
        f"  Usage: {psutil.virtual_memory().percent}%\n\n"
        f"**Uptime:** {uptime.days}d {uptime.seconds//3600}h"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def disk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    partitions = psutil.disk_partitions()
    msg = "💾 **Disk Usage:**\n\n"
    
    for partition in partitions:
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            msg += (
                f"📁 **{partition.device}** ({partition.mountpoint})\n"
                f"  Total: {format_bytes(usage.total)}\n"
                f"  Used: {format_bytes(usage.used)} ({usage.percent}%)\n"
                f"  Free: {format_bytes(usage.free)}\n\n"
            )
        except:
            pass
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def network_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    net_io = psutil.net_io_counters()
    msg = (
        "🌐 **Network Statistics**\n\n"
        f"📤 Sent: {format_bytes(net_io.bytes_sent)}\n"
        f"📥 Received: {format_bytes(net_io.bytes_recv)}\n"
        f"Packets Sent: {net_io.packets_sent:,}\n"
        f"Packets Received: {net_io.packets_recv:,}\n\n"
        f"Errors: In: {net_io.errin} | Out: {net_io.errout}\n"
        f"Dropped: In: {net_io.dropin} | Out: {net_io.dropout}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

def setup():
    return [
        CommandHandler("sysinfo", sysinfo_command),
        CommandHandler("disk", disk_command),
        CommandHandler("network", network_command)
    ]
