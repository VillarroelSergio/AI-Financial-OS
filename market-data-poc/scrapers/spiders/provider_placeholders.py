"""Scrapy spider skeletons for future legal review and targeted extraction."""
import scrapy


class _PlaceholderSpider(scrapy.Spider):
    custom_settings = {"ROBOTSTXT_OBEY": True, "DOWNLOAD_DELAY": 1.0}
    start_urls: list[str] = []

    def parse(self, response):
        yield {
            "provider": self.name,
            "url": response.url,
            "status": response.status,
            "title": response.css("title::text").get(default="").strip(),
        }


class MacrotrendsSpider(_PlaceholderSpider):
    name = "macrotrends"
    start_urls = ["https://www.macrotrends.net/"]


class CompaniesMarketCapSpider(_PlaceholderSpider):
    name = "companiesmarketcap"
    start_urls = ["https://companiesmarketcap.com/"]


class MarketScreenerSpider(_PlaceholderSpider):
    name = "marketscreener"
    start_urls = ["https://www.marketscreener.com/"]


class TradingViewSpider(_PlaceholderSpider):
    name = "tradingview"
    start_urls = ["https://www.tradingview.com/markets/"]


class StockAnalysisSpider(_PlaceholderSpider):
    name = "stockanalysis"
    start_urls = ["https://stockanalysis.com/"]


class BarchartSpider(_PlaceholderSpider):
    name = "barchart"
    start_urls = ["https://www.barchart.com/"]


class MarketBeatSpider(_PlaceholderSpider):
    name = "marketbeat"
    start_urls = ["https://www.marketbeat.com/"]


class DividendSpider(_PlaceholderSpider):
    name = "dividend_com"
    start_urls = ["https://www.dividend.com/"]


class ETFSpider(_PlaceholderSpider):
    name = "etf_com"
    start_urls = ["https://www.etf.com/"]


class JustETFSpider(_PlaceholderSpider):
    name = "justetf"
    start_urls = ["https://www.justetf.com/"]


class MorningstarSpider(_PlaceholderSpider):
    name = "morningstar"
    start_urls = ["https://www.morningstar.com/"]


class NasdaqPagesSpider(_PlaceholderSpider):
    name = "nasdaq_pages"
    start_urls = ["https://www.nasdaq.com/market-activity"]
