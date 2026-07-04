"""Runner de ingesta — orquesta catalog → fetch → quality → persist.

Punto de entrada para los comandos CLI market:intelligence:update.
"""
from __future__ import annotations

import importlib
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.modules.market_intelligence.catalog.loader import CatalogLoader
from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.orchestrator import (
    CatalogFetchResult,
    ProviderOrchestrator,
)

logger = logging.getLogger("market_intelligence.runner")

# Map provider_id → módulo del adapter
_ADAPTER_MAP: dict[str, str] = {
    "bde": "app.modules.market_intelligence.ingestion.adapters.spain.bde",
    "ine": "app.modules.market_intelligence.ingestion.adapters.spain.ine",
    "cnmv": "app.modules.market_intelligence.ingestion.adapters.spain.cnmv",
    "bme": "app.modules.market_intelligence.ingestion.adapters.spain.bme",
    "tesoro": "app.modules.market_intelligence.ingestion.adapters.spain.tesoro",
    "ree": "app.modules.market_intelligence.ingestion.adapters.spain.ree",
    "aemet": "app.modules.market_intelligence.ingestion.adapters.spain.aemet",
    "seguridad_social": "app.modules.market_intelligence.ingestion.adapters.spain.seguridad_social",
    "agencia_tributaria": "app.modules.market_intelligence.ingestion.adapters.spain.agencia_tributaria",
    "ecb": "app.modules.market_intelligence.ingestion.adapters.europe.ecb",
    "eurostat": "app.modules.market_intelligence.ingestion.adapters.europe.eurostat",
    "oecd": "app.modules.market_intelligence.ingestion.adapters.europe.oecd",
    "bis": "app.modules.market_intelligence.ingestion.adapters.europe.bis",
    "european_commission": "app.modules.market_intelligence.ingestion.adapters.europe.european_commission",
    "eur_lex": "app.modules.market_intelligence.ingestion.adapters.europe.eur_lex",
    "fred": "app.modules.market_intelligence.ingestion.adapters.usa.fred",
    "edgar": "app.modules.market_intelligence.ingestion.adapters.usa.edgar",
    "bls": "app.modules.market_intelligence.ingestion.adapters.usa.bls",
    "treasury": "app.modules.market_intelligence.ingestion.adapters.usa.treasury",
    "bea": "app.modules.market_intelligence.ingestion.adapters.usa.bea",
    "census": "app.modules.market_intelligence.ingestion.adapters.usa.census",
    "eia": "app.modules.market_intelligence.ingestion.adapters.usa.eia",
    "world_bank": "app.modules.market_intelligence.ingestion.adapters.global_.world_bank",
    "imf": "app.modules.market_intelligence.ingestion.adapters.global_.imf",
    "coingecko": "app.modules.market_intelligence.ingestion.adapters.global_.coingecko",
    "stooq": "app.modules.market_intelligence.ingestion.adapters.global_.stooq",
    "alpha_vantage": "app.modules.market_intelligence.ingestion.adapters.global_.alpha_vantage",
    "finnhub": "app.modules.market_intelligence.ingestion.adapters.global_.finnhub",
    "fmp": "app.modules.market_intelligence.ingestion.adapters.global_.fmp",
    "twelvedata": "app.modules.market_intelligence.ingestion.adapters.global_.twelvedata",
    "openfigi": "app.modules.market_intelligence.ingestion.adapters.global_.openfigi",
    "polygon": "app.modules.market_intelligence.ingestion.adapters.global_.polygon",
    "frankfurter": "app.modules.market_intelligence.ingestion.adapters.global_.frankfurter",
    "un_data": "app.modules.market_intelligence.ingestion.adapters.global_.un_data",
    "rss": "app.modules.market_intelligence.ingestion.adapters.rss.reader",
}


@dataclass
class IngestionSummary:
    run_id: str
    started_at: datetime
    finished_at: datetime
    total: int
    success: int
    failed: int
    fallbacks_used: int
    results: list[CatalogFetchResult] = field(default_factory=list)


# Fallos de import/instanciación del último build_adapters — expuestos en
# /ingest-status para que un bundle sin adapters (p.ej. PyInstaller sin
# hiddenimports) no vuelva a fallar en silencio.
ADAPTER_LOAD_ERRORS: dict[str, str] = {}


def build_adapters(provider_ids: list[str] | None = None) -> list[BaseAdapter]:
    """Instancia los adapters para los provider_ids dados (o todos si None)."""
    ids = provider_ids or list(_ADAPTER_MAP.keys())
    ADAPTER_LOAD_ERRORS.clear()
    adapters: list[BaseAdapter] = []
    for pid in ids:
        module_path = _ADAPTER_MAP.get(pid)
        if not module_path:
            continue
        try:
            module = importlib.import_module(module_path)
            adapter_cls = getattr(module, "Adapter", None)
            if adapter_cls is None:
                candidates = [
                    v for v in vars(module).values()
                    if isinstance(v, type) and issubclass(v, BaseAdapter) and v is not BaseAdapter
                ]
                adapter_cls = candidates[0] if candidates else None
            if adapter_cls is None:
                continue
            adapters.append(adapter_cls())
        except Exception as exc:
            ADAPTER_LOAD_ERRORS[pid] = str(exc)
            logger.warning("Could not load adapter '%s': %s", pid, exc)
    return adapters


def run_ingestion(
    category: str | None = None,
    priority: str | None = None,
    dashboard: bool = False,
    dry_run: bool = False,
) -> IngestionSummary:
    """Ejecuta la ingesta completa o filtrada y persiste en DuckDB."""
    # Lazy imports — these modules may not exist yet (Tasks 6-7)
    try:
        from app.modules.market_intelligence.quality.engine import QualityEngine
        quality_engine = QualityEngine()
    except ImportError:
        quality_engine = None

    try:
        from app.modules.market_intelligence.storage import repository as _repo
        repo = _repo
    except ImportError:
        repo = None

    run_id = str(uuid.uuid4())[:8]
    started_at = datetime.now(timezone.utc)

    loader = CatalogLoader()
    indicators = loader.load_all()
    if category:
        indicators = [i for i in indicators if i.category == category]
    if dashboard:
        indicators = [i for i in indicators if i.dashboard]
    if priority:
        indicators = [i for i in indicators if i.priority == priority]

    adapters = build_adapters()
    orchestrator = ProviderOrchestrator(adapters)

    results: list[CatalogFetchResult] = []
    success = 0
    failed = 0
    fallbacks = 0

    # Fetch en paralelo (HTTP-bound); la persistencia sigue secuencial porque
    # DuckDB comparte una única conexión de escritura.
    with ThreadPoolExecutor(max_workers=8) as pool:
        fetched = list(pool.map(orchestrator.fetch_indicator, indicators))

    for indicator, result in zip(indicators, fetched):
        results.append(result)

        if result.adapter_result.success:
            success += 1
            if result.fallback_used:
                fallbacks += 1
            if not dry_run and quality_engine is not None and repo is not None:
                quality_result = quality_engine.score(result, indicator)
                repo.persist_fetch_result(result, quality_result, run_id)
        else:
            failed += 1
            if not dry_run and repo is not None:
                repo.log_provider_health(
                    provider_id=result.provider_used,
                    catalog_item_id=indicator.id,
                    status="error",
                    latency_ms=int(result.adapter_result.latency_ms),
                    error_message=result.adapter_result.error,
                )

        logger.info(
            "run=%s indicator=%s provider=%s success=%s fallback=%s",
            run_id, indicator.id, result.provider_used,
            result.adapter_result.success, result.fallback_used,
        )

    return IngestionSummary(
        run_id=run_id,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        total=len(indicators),
        success=success,
        failed=failed,
        fallbacks_used=fallbacks,
        results=results,
    )
