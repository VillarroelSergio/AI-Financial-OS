from adapters.catalog import PublicDatasetAdapter


class EURLexAdapter(PublicDatasetAdapter):
    name = "EUR-Lex"
    provider_id = "eur_lex"
    category = "macro"
    region = "Europe"
    base_url = "https://eur-lex.europa.eu/eli-register/about.html"
    capabilities = ("macro", "news", "regulatory")
    priority = "fallback"
    update_frequency = "daily"
    historical_depth_years = 30
    notes = "EU legal and regulatory datasets relevant for market intelligence."


Adapter = EURLexAdapter
