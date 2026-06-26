from app.modules.market_intelligence.ingestion.adapters.catalog import PublicDatasetAdapter


class AgenciaTributariaAdapter(PublicDatasetAdapter):
    name = "Agencia Tributaria"
    provider_id = "agencia_tributaria"
    category = "macro"
    region = "Spain"
    base_url = "https://sede.agenciatributaria.gob.es/Sede/datosabiertos/catalogo/hacienda/datasets.html"
    capabilities = ("macro", "tax", "historical")
    priority = "secondary"
    update_frequency = "monthly"
    historical_depth_years = 20
    notes = "Public tax collection and fiscal statistics."


Adapter = AgenciaTributariaAdapter
