from adapters.catalog import PublicDatasetAdapter


class OpenCorporatesAdapter(PublicDatasetAdapter):
    name = "OpenCorporates"
    provider_id = "opencorporates"
    category = "companies"
    region = "Global"
    base_url = "https://api.opencorporates.com/v0.4/companies/search"
    capabilities = ("companies", "corporate_actions")
    priority = "fallback"
    update_frequency = "daily"
    historical_depth_years = 20
    notes = "Company registry search API."


Adapter = OpenCorporatesAdapter
