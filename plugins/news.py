# pyre-ignore-all-errors
import asyncio  # type: ignore  # pyre-ignore

import aiohttp  # type: ignore  # pyre-ignore
import requests  # type: ignore  # pyre-ignore
from telegram import Update  # type: ignore  # pyre-ignore
from telegram.ext import CommandHandler, ContextTypes  # type: ignore  # pyre-ignore

PLUGIN_DESCRIPTION = "Get tech news. Usage: /news"


async def _fetch_json(context: ContextTypes.DEFAULT_TYPE, url: str):
    session = context.application.bot_data.get("http_session")
    if isinstance(session, aiohttp.ClientSession):
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()
    return await asyncio.to_thread(lambda: requests.get(url, timeout=10).json())


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        story_ids = await _fetch_json(context, top_url)
        if not isinstance(story_ids, list) or not story_ids:
            await update.message.reply_text("Could not fetch news.")
            return

        story_ids = story_ids[:5]  # type: ignore  # pyre-ignore

        async def fetch_story(story_id: int):
            return await _fetch_json(context, f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")

        stories = await asyncio.gather(*(fetch_story(i) for i in story_ids), return_exceptions=True)

        news_items = []
        for story_id, story in zip(story_ids, stories):
            if isinstance(story, Exception):
                continue
            title = story.get("title")
            if not title:
                continue
            title = title[:80] + "..." if len(title) > 80 else title  # type: ignore  # pyre-ignore
            url = story.get("url", f"https://news.ycombinator.com/item?id={story_id}")
            news_items.append(f"📰 {title}\n🔗 {url}")

        if not news_items:
            await update.message.reply_text("Could not fetch news.")
            return

        msg = "📰 **Latest Tech News:**\n\n" + "\n\n".join(news_items)
        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


def setup():
    return [CommandHandler("news", news_command)]

