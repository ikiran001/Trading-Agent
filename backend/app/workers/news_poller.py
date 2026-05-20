import asyncio

from app.infrastructure.news.rss_fetcher import fetch_rss
from app.infrastructure.redis_bus import RedisBus
from app.services.sentiment import SentimentClassifier
from app.workers._runner import run_worker

_classifier = SentimentClassifier()
_seen: set[str] = set()


async def main_loop(settings):
    bus = await RedisBus.from_url(settings.redis_url)
    urls = settings.news_urls or [
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    ]
    while True:
        sentiments = []
        for url in urls:
            try:
                for article in fetch_rss(url):
                    if article.url in _seen or not article.url:
                        continue
                    _seen.add(article.url)
                    label = _classifier.classify(article.headline)
                    sentiments.append(label)
            except Exception:
                continue
        score = _classifier.score(sentiments[-20:] if sentiments else [])
        payload = {"score": score, "count": len(sentiments)}
        await bus.publish("sentiment:aggregate", payload)
        await bus.set_cache("cache:sentiment:aggregate", payload)
        await asyncio.sleep(60)


def main():
    asyncio.run(run_worker(main_loop))


if __name__ == "__main__":
    main()
