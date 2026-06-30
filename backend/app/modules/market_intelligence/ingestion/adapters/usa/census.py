from app.modules.market_intelligence.ingestion.adapters.catalog import PublicDatasetAdapter


class CensusAdapter(PublicDatasetAdapter):
    name = "Census Bureau"
    provider_id = "census"
    category = "macro"
    region = "USA"
    base_url = "https://api.census.gov/data.html"
    capabilities = ("macro", "housing", "retail", "historical")
    priority = "secondary"
    update_frequency = "monthly"
    historical_depth_years = 30
    notes = "US Census public datasets."


Adapter = CensusAdapter
