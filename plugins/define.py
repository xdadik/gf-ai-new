# pyre-ignore-all-errors
import asyncio  # type: ignore  # pyre-ignore

import aiohttp  # type: ignore  # pyre-ignore
import requests  # type: ignore  # pyre-ignore
from telegram import Update  # type: ignore  # pyre-ignore
from telegram.ext import CommandHandler, ContextTypes  # type: ignore  # pyre-ignore

PLUGIN_DESCRIPTION = "Dictionary lookup. Usage: /define <word>"


async def _fetch_json(context: ContextTypes.DEFAULT_TYPE, url: str) -> dict:  # type: ignore  # pyre-ignore
    session = context.application.bot_data.get("http_session")
    if isinstance(session, aiohttp.ClientSession):
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()
    return await asyncio.to_thread(lambda: requests.get(url, timeout=10).json())


async def define_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /define <word>")
        return

    word = " ".join(context.args).lower()
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        payload = await _fetch_json(context, url)
        if not isinstance(payload, list) or not payload:
            await update.message.reply_text(f"Could not find '{word}'")
            return

        data = payload[0]
        msg_lines = [f"📖 **{(data.get('word') or word).capitalize()}**"]

        for meaning in (data.get("meanings") or [])[:2]:  # type: ignore  # pyre-ignore
            part = meaning.get("partOfSpeech") or ""
            defs = meaning.get("definitions") or []
            if defs:
                msg_lines.append(f"\n_{part}_")
                for i, defn in enumerate(defs[:2], 1):  # type: ignore  # pyre-ignore
                    msg_lines.append(f"{i}. {defn.get('definition', '')}")
                    ex = defn.get("example")
                    if ex:
                        msg_lines.append(f"   _\"{ex}\"_")

        for ph in data.get("phonetics") or []:  # type: ignore  # pyre-ignore
            if ph.get("text"):
                msg_lines.append(f"\n🔊 {ph['text']}")
                break

        await update.message.reply_text("\n".join(msg_lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


def setup():
    return [CommandHandler("define", define_command)]

