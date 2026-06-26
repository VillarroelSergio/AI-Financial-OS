# Scraping

Scrapy is available for scraper-backed fallbacks.

Prepared target groups:

- Yahoo
- Investing
- Macrotrends
- CompaniesMarketCap
- MarketScreener
- TradingView
- StockAnalysis
- Barchart
- MarketBeat
- Dividend.com
- ETF.com
- JustETF
- Morningstar, only where legally allowed
- Nasdaq pages

Rules:

- Prefer official public APIs, CSV downloads and RSS feeds before scraping.
- Check robots.txt and terms before enabling spiders broadly.
- Keep scrapers as fallback providers, not primary sources, unless the source explicitly permits automated access.
- Normalize scraper output into the same models as API adapters.
