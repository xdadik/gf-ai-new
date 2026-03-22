# pyre-ignore-all-errors
import asyncio  # type: ignore  # pyre-ignore

import aiohttp  # type: ignore  # pyre-ignore
import requests  # type: ignore  # pyre-ignore
from telegram import Update  # type: ignore  # pyre-ignore
from telegram.ext import CommandHandler, ContextTypes  # type: ignore  # pyre-ignore

PLUGIN_DESCRIPTION = "Get cryptocurrency prices using /crypto <coin_id>"


async def _fetch_json(context: ContextTypes.DEFAULT_TYPE, url: str) -> dict:  # type: ignore  # pyre-ignore
    session = context.application.bot_data.get("http_session")
    if isinstance(session, aiohttp.ClientSession):
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()
    return await asyncio.to_thread(lambda: requests.get(url, timeout=10).json())


async def crypto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches crypto price using CoinGecko API."""
    if not context.args:
        await update.message.reply_text("Usage: /crypto bitcoin (or ethereum, dogecoin, etc.)")
        return

    coin_id = context.args[0].lower()
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        f"?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
    )
    try:
        data = await _fetch_json(context, url)
        if coin_id not in data:
            await update.message.reply_text(f"Could not find coin: {coin_id}")
            return

        price = data[coin_id]["usd"]
        change_24h = data[coin_id].get("usd_24h_change", 0)
        trend = "📈" if change_24h >= 0 else "📉"
        msg = (
            f"🪙 **{coin_id.capitalize()}**\n\n"
            f"Price: ${price:,.2f}\n"
            f"24h Change: {change_24h:.2f}% {trend}"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error fetching crypto data: {e}")


def setup():
    return [CommandHandler("crypto", crypto_command)]

