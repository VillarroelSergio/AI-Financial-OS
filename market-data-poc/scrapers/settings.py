"""Scrapy settings for market_data_poc scrapers."""

BOT_NAME = "market_data_poc"

SPIDER_MODULES = ["scrapers.spiders"]
NEWSPIDER_MODULE = "scrapers.spiders"

ROBOTSTXT_OBEY = True

DOWNLOAD_DELAY = 2

AUTOTHROTTLE_ENABLED = True

LOG_LEVEL = "ERROR"
