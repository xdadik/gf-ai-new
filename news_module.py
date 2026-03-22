# pyre-ignore-all-errors
"""
News Module for Nova
Allows Nova to fetch and summarize news for the user
"""

import asyncio  # type: ignore  # pyre-ignore
import json  # type: ignore  # pyre-ignore
import os  # type: ignore  # pyre-ignore
from datetime import datetime, timedelta  # type: ignore  # pyre-ignore
from typing import Dict, List, Optional  # type: ignore  # pyre-ignore

import aiohttp  # type: ignore  # pyre-ignore
import feedparser  # type: ignore  # pyre-ignore

# News API Configuration
# News API Configuration - loaded at runtime so dotenv values work
def _get_news_api_key() -> str:
    return os.getenv("NEWS_API_KEY", "")

NEWS_API_KEY = _get_news_api_key()
NEWS_SOURCES = {
    "tech": [
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://www.theverge.com/rss/index.xml",
        "https://techcrunch.com/feed/",
    ],
    "general": [
        "http://feeds.bbci.co.uk/news/rss.xml",
        "https://rss.cnn.com/rss/edition.rss",
    ],
    "science": [
        "https://www.sciencedaily.com/rss/all.xml",
        "https://feeds.nationalgeographic.com/ng/News/News_Main.rss",
    ],
    "gaming": [
        "https://www.pcgamer.com/rss/",
        "https://feeds.ign.com/ign/all",
    ],
}


class NewsChecker:
    """News checking and fetching functionality for Nova"""

    def __init__(self):
        self.cache: Dict[str, dict] = {}  # type: ignore  # pyre-ignore
        self.cache_time: timedelta = timedelta(minutes=30)
        self.last_fetch: Optional[datetime] = None  # type: ignore  # pyre-ignore

    async def fetch_news(self, category: str = "general", limit: int = 5) -> str:  # type: ignore  # pyre-ignore
        """Fetch news from RSS feeds for a specific category"""
        if category not in NEWS_SOURCES:
            return f"Unknown category: {category}. Available: {', '.join(NEWS_SOURCES.keys())}"

        # Check cache
        if self._is_cache_valid(category):
            return self._format_cached_news(category, limit)

        all_entries = []
        async with aiohttp.ClientSession() as session:
            for feed_url in NEWS_SOURCES[category]:  # type: ignore  # pyre-ignore
                try:
                    async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            content = await response.text()
                            feed = feedparser.parse(content)
                            for entry in feed.entries[:limit]:  # type: ignore  # pyre-ignore
                                all_entries.append({
                                    "title": entry.get("title", "No title"),
                                    "summary": entry.get("summary", "")[:200] + "..." if len(entry.get("summary", "")) > 200 else entry.get("summary", ""),  # type: ignore  # pyre-ignore
                                    "link": entry.get("link", ""),
                                    "published": entry.get("published", "Unknown date"),
                                    "source": feed.feed.get("title", "Unknown source"),
                                })
                except Exception as e:
                    continue  # Skip failed feeds

        # Sort by date and limit results
        all_entries = sorted(all_entries, key=lambda x: x.get("published", ""), reverse=True)[:limit]  # type: ignore  # pyre-ignore

        # Cache results
        self.cache[category] = {
            "entries": all_entries,
            "timestamp": datetime.now(),
        }

        return self._format_news(all_entries, category)

    async def fetch_news_api(self, query: str = "", category: str = "", limit: int = 5) -> str:  # type: ignore  # pyre-ignore
        """Fetch news using NewsAPI (requires API key)"""
        api_key = os.getenv("NEWS_API_KEY", "") or NEWS_API_KEY
        if not api_key:
            return "News API key not configured. Please set NEWS_API_KEY in .env file."

        url = "https://newsapi.org/v2/top-headlines" if not query else "https://newsapi.org/v2/everything"
        params = {
            "apiKey": api_key,
            "pageSize": limit,
            "language": "en",
        }

        if query:
            params["q"] = query
            params["sortBy"] = "relevancy"
        if category:
            params["category"] = category

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get("articles", [])
                        return self._format_api_news(articles, query or category)
                    else:
                        return f"Failed to fetch news: HTTP {response.status}"
            except Exception as e:
                return f"Error fetching news: {e}"

    async def check_specific_topic(self, topic: str, limit: int = 3) -> str:  # type: ignore  # pyre-ignore
        """Check news for a specific topic"""
        if NEWS_API_KEY:
            return await self.fetch_news_api(query=topic, limit=limit)
        else:
            # Fallback to searching in cached feeds
            results = []
            for category in NEWS_SOURCES.keys():
                cached = self.cache.get(category, {}).get("entries", [])
                for entry in cached:
                    if topic.lower() in entry.get("title", "").lower() or topic.lower() in entry.get("summary", "").lower():
                        results.append(entry)

            if results:
                return self._format_news(results[:limit], f"topic: {topic}")  # type: ignore  # pyre-ignore
            else:
                # Fetch fresh news
                await self.fetch_news("general", 10)
                return await self.check_specific_topic(topic, limit)

    async def get_trending_topics(self) -> str:  # type: ignore  # pyre-ignore
        """Get trending news topics"""
        if NEWS_API_KEY:
            return await self.fetch_news_api(category="general", limit=10)
        else:
            return await self.fetch_news("general", 10)

    def _is_cache_valid(self, category: str) -> bool:  # type: ignore  # pyre-ignore
        """Check if cached news is still valid"""
        if category not in self.cache:
            return False
        cache_time = self.cache[category].get("timestamp")
        if not cache_time:
            return False
        return datetime.now() - cache_time < self.cache_time

    def _format_cached_news(self, category: str, limit: int) -> str:  # type: ignore  # pyre-ignore
        """Format cached news"""
        entries = self.cache[category].get("entries", [])[:limit]  # type: ignore  # pyre-ignore
        return self._format_news(entries, category, cached=True)

    def _format_news(self, entries: List[dict], category: str, cached: bool = False) -> str:  # type: ignore  # pyre-ignore
        """Format news entries for display"""
        if not entries:
            return f"No news found for category: {category}"

        header = f"📰 **Latest {category.capitalize()} News**"
        if cached:
            header += " (Cached)"
        header += "\n\n"

        lines = [header]
        for i, entry in enumerate(entries, 1):
            title = entry.get("title", "No title")
            summary = entry.get("summary", "")
            source = entry.get("source", "Unknown")
            published = entry.get("published", "")

            lines.append(f"{i}. **{title}**")
            if summary:
                lines.append(f"   _{summary}_")
            lines.append(f"   📰 {source} | {published}\n")

        return "\n".join(lines)

    def _format_api_news(self, articles: List[dict], query: str) -> str:  # type: ignore  # pyre-ignore
        """Format NewsAPI articles"""
        if not articles:
            return f"No news found for: {query}"

        lines = [f"📰 **News Results: {query.capitalize()}**\n"]  # type: ignore  # pyre-ignore
        for i, article in enumerate(articles[:5], 1):  # type: ignore  # pyre-ignore
            title = article.get("title", "No title")
            description = article.get("description", "") or ""
            source = article.get("source", {}).get("name", "Unknown")
            published = article.get("publishedAt", "")[:10]  # type: ignore  # pyre-ignore

            lines.append(f"{i}. **{title}**")
            if description:
                lines.append(f"   _{description[:150]}..._")  # type: ignore  # pyre-ignore
            lines.append(f"   📰 {source} | {published}\n")

        return "\n".join(lines)

    async def summarize_news(self, url: str) -> str:  # type: ignore  # pyre-ignore
        """Fetch and summarize a specific news article"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        content = await response.text()
                        # Extract basic text (simplified)
                        return f"📄 **Article Content**\n\n(Use the summarize command for detailed analysis)\n\nSource: {url}"
                    else:
                        return f"Could not fetch article: HTTP {response.status}"
            except Exception as e:
                return f"Error fetching article: {e}"


# Global instance
news_checker = NewsChecker()


# Tool functions for Nova to use
async def get_news(category: str = "general", limit: int = 5, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    """Get news for a specific category"""
    return await news_checker.fetch_news(category, limit)


async def search_news(query: str, limit: int = 5, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    """Search news for a specific topic"""
    return await news_checker.check_specific_topic(query, limit)


async def get_trending_news(user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    """Get trending news"""
    return await news_checker.get_trending_topics()


async def get_tech_news(limit: int = 5, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    """Get technology news"""
    return await news_checker.fetch_news("tech", limit)


async def get_science_news(limit: int = 5, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    """Get science news"""
    return await news_checker.fetch_news("science", limit)


async def get_gaming_news(limit: int = 5, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    """Get gaming news"""
    return await news_checker.fetch_news("gaming", limit)

