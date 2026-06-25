from adapters.catalog import PublicDatasetAdapter


class EuropeanCommissionAdapter(PublicDatasetAdapter):
    name = "European Commission Data"
    provider_id = "european_commission"
    category = "macro"
    region = "Europe"
    base_url = "https://data.europa.eu/data/datasets?locale=en"
    capabilities = ("macro", "economic_calendar", "historical")
    priority = "fallback"
    update_frequency = "monthly"
    historical_depth_years = 20
    notes = "European Commission and EU open data portal datasets."


Adapter = EuropeanCommissionAdapter
