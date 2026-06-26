from dataclasses import dataclass, field


@dataclass
class ProviderEvaluation:
    provider: str
    score_total: float              # 0-100
    data_quality: float             # 0-100, weight 25%
    reliability: float              # 0-100, weight 20%
    coverage_breadth: float         # 0-100, weight 15%
    geo_coverage: float             # 0-100, weight 10%
    historical_depth: float         # 0-100, weight 10%
    update_frequency: float         # 0-100, weight 10%
    latency_score: float            # 0-100, weight 5%
    integration_complexity: float   # 0-100, weight 3%
    legal_risk: float               # 0-100, weight 2% (0=safe, 100=risky)
    recommendation: str             # "principal"|"secundario"|"fallback"|"descartado"
    adapter_result: object          # AdapterResult reference


@dataclass
class CoverageReport:
    total_providers: int
    successful: int
    failed: int
    unavailable: int
    evaluations: list               # list[ProviderEvaluation]
    by_region: dict                 # region -> list[ProviderEvaluation]
    by_category: dict               # category -> list[ProviderEvaluation]
    total_time_ms: float
