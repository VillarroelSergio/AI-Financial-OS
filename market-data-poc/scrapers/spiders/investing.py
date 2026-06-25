"""Investing.com Scrapy spider — fallback scraper for world indices."""
import scrapy


class InvestingSpider(scrapy.Spider):
    name = "investing"
    custom_settings = {"ROBOTSTXT_OBEY": True}
    start_urls = ["https://www.investing.com/indices/world-indices"]

    def parse(self, response):
        for row in response.css("table.genTbl tr"):
            name = row.css("td.bold::text").get()
            price = row.css("td:nth-child(3)::text").get()
            if name and price:
                yield {"name": name.strip(), "price": price.strip(), "source": "investing"}
