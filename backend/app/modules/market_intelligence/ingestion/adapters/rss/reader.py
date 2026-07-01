"""RSS adapter — aggregates financial news from multiple RSS feeds."""
import time
import feedparser
from datetime import datetime, timezone

from app.modules.market_intelligence.ingestion.models import AdapterResult
from app.modules.market_intelligence.ingestion.models import NewsItem
from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter

RSS_FEEDS = [
    {"name": "Expansión", "url": "https://www.expansion.com/rss/portada.xml", "category": "finance"},
    {"name": "Cinco Días", "url": "https://cincodias.elpais.com/rss/cincodias_mercados.xml", "category": "markets"},
    {"name": "El Economista", "url": "https://www.eleconomista.es/rss/rss-portada-mercados.php", "category": "markets"},
    {"name": "Reuters Markets", "url": "https://feeds.reuters.com/reuters/businessNews", "category": "business"},
    {"name": "CNBC Markets", "url": "https://feeds.nbcnews.com/nbcnews/public/news", "category": "markets"},
    {"name": "ECB News", "url": "https://www.ecb.europa.eu/rss/press.html", "category": "central_bank"},
    {"name": "Federal Reserve", "url": "https://www.federalreserve.gov/feeds/press_all.xml", "category": "central_bank"},
]

EXTRA_RSS_FEEDS = [
    {"name": "CNBC Markets", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html", "category": "markets"},
    {"name": "Financial Times Markets", "url": "https://www.ft.com/markets?format=rss", "category": "markets"},
    {"name": "MarketWatch", "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories", "category": "markets"},
    {"name": "Bloomberg Markets", "url": "https://feeds.bloomberg.com/markets/news.rss", "category": "markets"},
    {"name": "Investing", "url": "https://www.investing.com/rss/news.rss", "category": "markets"},
    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/news/rssindex", "category": "markets"},
    {"name": "Seeking Alpha", "url": "https://seekingalpha.com/market_currents.xml", "category": "markets"},
]


class RSSAdapter(BaseAdapter):
    name = "RSS Feeds"
    category = "news"
    region = "Global"
    requires_api_key = False

    def fetch(self) -> AdapterResult:
        metadata = self._make_metadata(
            base_url="multiple",
            method="rss",
            license="Public RSS",
        )
        t0 = time.time()
        records = []
        retrieved_at = datetime.now(timezone.utc)

        feeds = RSS_FEEDS + [feed for feed in EXTRA_RSS_FEEDS if feed["url"] not in {f["url"] for f in RSS_FEEDS}]
        for feed_info in feeds:
            try:
                feed = feedparser.parse(feed_info["url"])
                for entry in feed.entries:
                    title = getattr(entry, "title", "")
                    url = getattr(entry, "link", "")
                    published_at = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        try:
                            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                        except Exception:
                            published_at = None

                    records.append(
                        NewsItem(
                            provider=self.name,
                            source=feed_info["url"],
                            retrieved_at=retrieved_at,
                            country="GLOBAL",
                            region=self.region,
                            confidence_score=0.8,
                            title=title,
                            published_at=published_at,
                            source_name=feed_info["name"],
                            url=url,
                            category=feed_info["category"],
                            related_asset="",
                        )
                    )
            except Exception:
                # feedparser handles errors gracefully; skip feeds that fail
                continue

        latency_ms = (time.time() - t0) * 1000

        if not records:
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error="No RSS entries retrieved",
                latency_ms=latency_ms,
                raw_sample=None,
                metadata=metadata,
            )

        return AdapterResult(
            provider=self.name,
            success=True,
            records=records,
            error=None,
            latency_ms=latency_ms,
            raw_sample={"feeds_attempted": len(feeds), "items_retrieved": len(records)},
            metadata=metadata,
        )
