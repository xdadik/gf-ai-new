# pyre-ignore-all-errors
import asyncio  # type: ignore  # pyre-ignore

import aiohttp  # type: ignore  # pyre-ignore
import requests  # type: ignore  # pyre-ignore
from telegram import Update  # type: ignore  # pyre-ignore
from telegram.ext import CommandHandler, ContextTypes  # type: ignore  # pyre-ignore

PLUGIN_DESCRIPTION = "Translate text. Usage: /translate <from> <to> <text>"


async def _post_json(context: ContextTypes.DEFAULT_TYPE, url: str, payload: dict) -> dict:  # type: ignore  # pyre-ignore
    session = context.application.bot_data.get("http_session")
    if isinstance(session, aiohttp.ClientSession):
        async with session.post(url, json=payload) as resp:
            resp.raise_for_status()
            return await resp.json()
    return await asyncio.to_thread(lambda: requests.post(url, json=payload, timeout=10).json())


async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "🌐 Translate: /translate <source> <target> <text>\nExample: /translate en es Hello world"
        )
        return

    source_lang = context.args[0].lower()
    target_lang = context.args[1].lower()
    text = " ".join(context.args[2:])  # type: ignore  # pyre-ignore

    url = "https://libretranslate.com/translate"
    payload = {"q": text, "source": source_lang, "target": target_lang, "format": "text"}

    try:
        result = await _post_json(context, url, payload)
        translated = result.get("translatedText", "Translation failed")
        await update.message.reply_text(
            f"🌐 **Translation**\n\n📝 Original ({source_lang}): {text}\n\n✨ Translated ({target_lang}): {translated}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


def setup():
    return [CommandHandler("translate", translate_command)]

