# Coverage

Normalized model coverage:

- `Dividend`
- `ETF`
- `Fund`
- `Commodity`
- `Currency`
- `YieldCurve`
- `EconomicCalendar`
- `MacroSeries`
- `CorporateAction`
- `MarketNews`
- `ProviderHealth`
- `ProviderCapability`
- `ProviderCoverage`
- `ProviderScore`

Capability coverage:

- Stocks, ETF, funds, macro, bonds, commodities, currencies, crypto, news
- Dividends, earnings, calendar, historical, intraday and realtime where providers support it

Known gaps:

- Some free public sources expose catalogs or landing pages rather than clean bulk APIs.
- Several realtime, dividend, earnings and ETF composition endpoints require freemium API keys.
- Scraped providers need legal and robots.txt review before broad production use.
