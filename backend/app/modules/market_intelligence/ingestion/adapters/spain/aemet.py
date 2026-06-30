from app.modules.market_intelligence.ingestion.adapters.catalog import PublicDatasetAdapter


class AEMETAdapter(PublicDatasetAdapter):
    name = "AEMET"
    provider_id = "aemet"
    category = "macro"
    region = "Spain"
    base_url = "https://www.aemet.es/es/datos_abiertos/AEMET_OpenData"
    capabilities = ("macro", "economic_calendar")
    priority = "fallback"
    method = "api"
    notes = "OpenData meteorological datasets useful for energy, agriculture and climate macro context."


Adapter = AEMETAdapter
