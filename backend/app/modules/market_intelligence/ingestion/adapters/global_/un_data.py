from app.modules.market_intelligence.ingestion.adapters.catalog import PublicDatasetAdapter


class UNDataAdapter(PublicDatasetAdapter):
    name = "UN Data"
    provider_id = "un_data"
    category = "macro"
    region = "Global"
    base_url = "http://data.un.org"
    capabilities = ("macro", "historical")
    priority = "fallback"
    update_frequency = "yearly"
    historical_depth_years = 60
    notes = "United Nations public macro datasets."


Adapter = UNDataAdapter
