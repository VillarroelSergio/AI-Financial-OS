from app.modules.market_intelligence.ingestion.adapters.catalog import PublicDatasetAdapter


class BISAdapter(PublicDatasetAdapter):
    name = "BIS"
    provider_id = "bis"
    category = "macro"
    region = "Global"
    base_url = "https://stats.bis.org/api/v1"
    capabilities = ("macro", "bonds", "currency", "historical")
    priority = "secondary"
    update_frequency = "monthly"
    historical_depth_years = 40
    notes = "Bank for International Settlements public statistics API."


Adapter = BISAdapter
