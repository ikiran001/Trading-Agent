from dataclasses import dataclass
from datetime import datetime

import feedparser


@dataclass
class NewsArticle:
    source: str
    url: str
    headline: str
    published_at: datetime | None


def fetch_rss(url: str, source: str = "rss") -> list[NewsArticle]:
    feed = feedparser.parse(url)
    articles: list[NewsArticle] = []
    for entry in feed.entries[:20]:
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])
        articles.append(
            NewsArticle(
                source=source,
                url=entry.get("link", ""),
                headline=entry.get("title", ""),
                published_at=published,
            )
        )
    return articles
