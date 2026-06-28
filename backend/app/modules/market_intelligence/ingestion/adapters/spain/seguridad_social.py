from app.modules.market_intelligence.ingestion.adapters.catalog import PublicDatasetAdapter


class SeguridadSocialAdapter(PublicDatasetAdapter):
    name = "Seguridad Social"
    provider_id = "seguridad_social"
    category = "macro"
    region = "Spain"
    base_url = "https://www.seg-social.es/wps/portal/wss/internet/EstadisticasPresupuestosEstudios/Estadisticas"
    capabilities = ("macro", "employment", "historical")
    priority = "secondary"
    method = "api"
    update_frequency = "monthly"
    historical_depth_years = 20
    notes = "Public affiliation, pensions and labour statistics."


Adapter = SeguridadSocialAdapter
