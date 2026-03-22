# pyre-ignore-all-errors
import asyncio  # type: ignore  # pyre-ignore

import aiohttp  # type: ignore  # pyre-ignore
import requests  # type: ignore  # pyre-ignore
from telegram import Update  # type: ignore  # pyre-ignore
from telegram.ext import CommandHandler, ContextTypes  # type: ignore  # pyre-ignore

PLUGIN_DESCRIPTION = "Get current weather info using /weather <city>"


async def _fetch_text(context: ContextTypes.DEFAULT_TYPE, url: str) -> str:  # type: ignore  # pyre-ignore
    session = context.application.bot_data.get("http_session")
    if isinstance(session, aiohttp.ClientSession):
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.text()
    return await asyncio.to_thread(lambda: requests.get(url, timeout=10).text)


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches weather for a given city using wttr.in (no API key needed)."""
    if not context.args:
        await update.message.reply_text("Please provide a city. Usage: /weather <city>")
        return

    city = " ".join(context.args)
    url = f"https://wttr.in/{city}?format=%l:+%C+%t+(Feels+like:+%f)\nHumidity:+%h\nWind:+%w"

    try:
        weather_info = await _fetch_text(context, url)
        await update.message.reply_text(f"☁️ **Weather Info**\n\n{weather_info}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error fetching weather: {e}")


def setup():
    return [CommandHandler("weather", weather_command)]

