"""Yahoo Finance Scrapy spider — fallback scraper (not used in main run)."""
import scrapy


class YahooFinanceSpider(scrapy.Spider):
    name = "yahoo_finance"
    start_urls = ["https://finance.yahoo.com/markets/"]

    def parse(self, response):
        # Extract ticker symbols and prices from the markets page.
        # This is a fallback — mark as scraping method.
        for row in response.css("table tr"):
            symbol = row.css("td:first-child::text").get()
            price = row.css("td:nth-child(2)::text").get()
            if symbol and price:
                yield {"symbol": symbol.strip(), "price": price.strip(), "source": "yahoo_finance"}
