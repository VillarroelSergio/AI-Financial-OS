"""Financial Knowledge Service — orquesta el pipeline de conocimiento financiero."""
from __future__ import annotations
import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.modules.financial_knowledge._shared import now as _now
from app.modules.financial_knowledge.engines import economic_indicator_engine as eie
from app.modules.financial_knowledge.engines import financial_signal_engine as fse
from app.modules.financial_knowledge.engines import market_regime_engine as mre
from app.modules.financial_knowledge.engines import correlation_engine as ce
from app.modules.financial_knowledge.engines import personal_impact_engine as pie
from app.modules.financial_knowledge.engines import knowledge_graph_engine as kge
from app.modules.financial_knowledge.engines import ai_datasheet_generator as adg
from app.modules.financial_knowledge.schemas import (
    AIDatasheetOut, EconomicIndicatorInsightOut, FinancialSignalOut,
    KnowledgeSnapshotOut, MarketRegimeOut, PersonalImpactOut, RecomputeResultOut,
)

logger = logging.getLogger("financial_knowledge.service")


def recompute(db: Optional[Session] = None) -> RecomputeResultOut:
    """Ejecuta el pipeline completo de conocimiento financiero."""
    from app.modules.financial_knowledge.storage.repository import (
        save_insights, save_signals, save_regime, save_impacts,
        save_datasheet, save_knowledge_graph_nodes, save_knowledge_graph_edges,
    )
    errors: list[str] = []
    insights_count = signals_count = impacts_count = 0
    regime_computed = datasheet_generated = False

    try:
        insights = eie.compute_insights()
        insights_count = save_insights(insights)
    except Exception as e:
        logger.error("EconomicIndicatorEngine: %s", e)
        errors.append(f"economic_indicator_engine: {e}")
        insights = []

    try:
        signals = fse.compute_signals(insights=insights)
        signals_count = save_signals(signals)
    except Exception as e:
        logger.error("FinancialSignalEngine: %s", e)
        errors.append(f"financial_signal_engine: {e}")
        signals = []

    try:
        regime = mre.compute_regime(signals)
        save_regime(regime)
        regime_computed = True
    except Exception as e:
        logger.error("MarketRegimeEngine: %s", e)
        errors.append(f"market_regime_engine: {e}")
        regime = None

    try:
        ce.compute_correlations(signals)
    except Exception as e:
        logger.warning("CorrelationEngine: %s", e)

    try:
        impacts = pie.compute_personal_impacts(signals=signals, db=db)
        impacts_count = save_impacts(impacts)
    except Exception as e:
        logger.error("PersonalImpactEngine: %s", e)
        errors.append(f"personal_impact_engine: {e}")
        impacts = []

    try:
        nodes, edges = kge.build_knowledge_graph(insights, signals, regime, impacts)
        save_knowledge_graph_nodes(nodes)
        save_knowledge_graph_edges(edges)
    except Exception as e:
        logger.warning("KnowledgeGraphEngine: %s", e)

    try:
        datasheet = adg.generate_datasheet(insights, signals, regime, impacts)
        save_datasheet("daily", adg.datasheet_to_json(datasheet), datasheet.quality_score)
        datasheet_generated = True
    except Exception as e:
        logger.error("AIDatasheetGenerator: %s", e)
        errors.append(f"ai_datasheet_generator: {e}")

    return RecomputeResultOut(
        success=len(errors) == 0,
        message="Recomputación completada" if not errors else f"Completado con {len(errors)} errores",
        insights_computed=insights_count,
        signals_computed=signals_count,
        regime_computed=regime_computed,
        impacts_computed=impacts_count,
        datasheet_generated=datasheet_generated,
        errors=errors,
    )


def get_snapshot() -> KnowledgeSnapshotOut:
    from app.modules.financial_knowledge.storage.repository import (
        get_latest_insights, get_latest_signals, get_latest_regime, get_latest_impacts,
    )
    insights_rows = get_latest_insights(limit=20)
    signals_rows = get_latest_signals()
    regime_row = get_latest_regime()
    impacts_rows = get_latest_impacts()
    scores = [r.get("quality_score", 1.0) for r in insights_rows + signals_rows]
    quality = round(sum(scores) / len(scores), 3) if scores else 0.0
    return KnowledgeSnapshotOut(
        generated_at=_now().isoformat(),
        quality_score=quality,
        regime=MarketRegimeOut(**regime_row) if regime_row else None,
        signals=[FinancialSignalOut(**r) for r in signals_rows],
        insights=[EconomicIndicatorInsightOut(**r) for r in insights_rows],
        personal_impacts=[PersonalImpactOut(**r) for r in impacts_rows],
        warnings=[],
    )


def get_regime() -> Optional[MarketRegimeOut]:
    from app.modules.financial_knowledge.storage.repository import get_latest_regime
    row = get_latest_regime()
    return MarketRegimeOut(**row) if row else None


def get_signals() -> list[FinancialSignalOut]:
    from app.modules.financial_knowledge.storage.repository import get_latest_signals
    return [FinancialSignalOut(**r) for r in get_latest_signals()]


def get_personal_impacts() -> list[PersonalImpactOut]:
    from app.modules.financial_knowledge.storage.repository import get_latest_impacts
    return [PersonalImpactOut(**r) for r in get_latest_impacts()]


def get_ai_datasheet() -> Optional[AIDatasheetOut]:
    from app.modules.financial_knowledge.storage.repository import get_latest_datasheet
    row = get_latest_datasheet("daily")
    if row is None:
        return None
    data = json.loads(row["datasheet_json"])
    data["generated_at"] = row["generated_at"]
    data["quality_score"] = row["quality_score"]
    return AIDatasheetOut(**data)
