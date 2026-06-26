from app.modules.market_intelligence.ingestion.adapters.catalog import PublicDatasetAdapter


class BEAAdapter(PublicDatasetAdapter):
    name = "BEA"
    provider_id = "bea"
    category = "macro"
    region = "USA"
    base_url = "https://apps.bea.gov/api/data"
    capabilities = ("macro", "gdp", "historical")
    priority = "primary"
    update_frequency = "monthly"
    historical_depth_years = 90
    notes = "Bureau of Economic Analysis public API."


Adapter = BEAAdapter
