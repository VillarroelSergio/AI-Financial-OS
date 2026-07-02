"""Repository DuckDB para el Financial Knowledge Layer."""
from __future__ import annotations

import json
import logging
from typing import Optional

from app.core.duckdb import get_duckdb
from app.modules.financial_knowledge._shared import now as _now
from app.modules.financial_knowledge._shared import uid as _uid
from app.modules.financial_knowledge.storage.migrations import run_migrations

logger = logging.getLogger("financial_knowledge.repository")

_migrations_run = False


def _conn():
    global _migrations_run
    c = get_duckdb()
    if not _migrations_run:
        run_migrations(c)
        _migrations_run = True
    return c


def save_insights(insights: list) -> int:
    conn = _conn()
    count = 0
    for insight in insights:
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO fk_economic_indicator_insights
                (id, indicator_id, catalog_item_id, name, category, country, value, unit, period,
                 previous_value, change_abs, change_pct, trend, target_value, distance_to_target,
                 interpretation, severity, quality_score, source_provider, rule_id, computed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    insight.id, insight.indicator_id, insight.catalog_item_id,
                    insight.name, insight.category, insight.country,
                    insight.value, insight.unit, insight.period,
                    insight.previous_value, insight.change_abs, insight.change_pct,
                    insight.trend.value, insight.target_value, insight.distance_to_target,
                    insight.interpretation, insight.severity.value, insight.quality_score,
                    insight.source_provider, insight.rule_id,
                    insight.computed_at,
                ],
            )
            count += 1
        except Exception as e:
            logger.warning("Error guardando insight %s: %s", insight.id, e)
    return count


def get_latest_insights(limit: int = 50) -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        """
        SELECT id, indicator_id, catalog_item_id, name, category, country, value, unit, period,
               previous_value, change_abs, change_pct, trend, target_value, distance_to_target,
               interpretation, severity, quality_score, source_provider, rule_id, computed_at
        FROM fk_economic_indicator_insights
        ORDER BY computed_at DESC
        LIMIT ?
        """,
        [limit],
    ).fetchall()
    cols = ["id", "indicator_id", "catalog_item_id", "name", "category", "country",
            "value", "unit", "period", "previous_value", "change_abs", "change_pct",
            "trend", "target_value", "distance_to_target", "interpretation",
            "severity", "quality_score", "source_provider", "rule_id", "computed_at"]
    return [dict(zip(cols, r)) for r in rows]


def save_signals(signals: list) -> int:
    conn = _conn()
    count = 0
    for sig in signals:
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO fk_financial_signals
                (id, signal_type, name, category, description, direction, severity,
                 confidence_score, quality_score, affected_assets_json, affected_user_domains_json,
                 source_indicators_json, rule_id, computed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    sig.id, sig.signal_type, sig.name, sig.category, sig.description,
                    sig.direction.value, sig.severity.value,
                    sig.confidence_score, sig.quality_score,
                    json.dumps(sig.affected_assets),
                    json.dumps(sig.affected_user_domains),
                    json.dumps(sig.source_indicators),
                    sig.rule_id, sig.computed_at,
                ],
            )
            count += 1
        except Exception as e:
            logger.warning("Error guardando señal %s: %s", sig.id, e)
    return count


def get_latest_signals() -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        """
        SELECT id, signal_type, name, category, description, direction, severity,
               confidence_score, quality_score, affected_assets_json, affected_user_domains_json,
               source_indicators_json, rule_id, computed_at
        FROM fk_financial_signals
        QUALIFY ROW_NUMBER() OVER (PARTITION BY signal_type ORDER BY computed_at DESC) = 1
        ORDER BY computed_at DESC
        """
    ).fetchall()
    cols = ["id", "signal_type", "name", "category", "description", "direction", "severity",
            "confidence_score", "quality_score", "affected_assets_json", "affected_user_domains_json",
            "source_indicators_json", "rule_id", "computed_at"]
    result = []
    for r in rows:
        d = dict(zip(cols, r))
        d["affected_assets"] = json.loads(d.pop("affected_assets_json") or "[]")
        d["affected_user_domains"] = json.loads(d.pop("affected_user_domains_json") or "[]")
        d["source_indicators"] = json.loads(d.pop("source_indicators_json") or "[]")
        result.append(d)
    return result


def save_regime(regime) -> None:
    conn = _conn()
    conn.execute(
        """
        INSERT INTO fk_market_regimes
        (id, regime_type, risk_level, inflation_regime, rates_regime, growth_regime,
         market_trend, confidence_score, signals_used_json, explanation, computed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            regime.id, regime.regime_type,
            regime.risk_level.value, regime.inflation_regime.value,
            regime.rates_regime.value, regime.growth_regime.value,
            regime.market_trend.value, regime.confidence_score,
            json.dumps(regime.signals_used), regime.explanation, regime.computed_at,
        ],
    )


def get_latest_regime() -> Optional[dict]:
    conn = _conn()
    row = conn.execute(
        """
        SELECT id, regime_type, risk_level, inflation_regime, rates_regime, growth_regime,
               market_trend, confidence_score, signals_used_json, explanation, computed_at
        FROM fk_market_regimes
        ORDER BY computed_at DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return None
    cols = ["id", "regime_type", "risk_level", "inflation_regime", "rates_regime",
            "growth_regime", "market_trend", "confidence_score", "signals_used_json",
            "explanation", "computed_at"]
    d = dict(zip(cols, row))
    d["signals_used"] = json.loads(d.pop("signals_used_json") or "[]")
    return d


def save_impacts(impacts: list) -> int:
    conn = _conn()
    count = 0
    for impact in impacts:
        try:
            conn.execute(
                """
                INSERT INTO fk_personal_impacts
                (id, impact_type, user_domain, title, description, severity,
                 estimated_monthly_impact, estimated_portfolio_impact, currency,
                 related_accounts_json, related_holdings_json, related_goals_json,
                 source_signals_json, confidence_score, computed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    impact.id, impact.impact_type, impact.user_domain,
                    impact.title, impact.description, impact.severity.value,
                    impact.estimated_monthly_impact, impact.estimated_portfolio_impact,
                    impact.currency,
                    json.dumps(impact.related_accounts),
                    json.dumps(impact.related_holdings),
                    json.dumps(impact.related_goals),
                    json.dumps(impact.source_signals),
                    impact.confidence_score, impact.computed_at,
                ],
            )
            count += 1
        except Exception as e:
            logger.warning("Error guardando impacto %s: %s", impact.id, e)
    return count


def get_latest_impacts() -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        """
        SELECT id, impact_type, user_domain, title, description, severity,
               estimated_monthly_impact, estimated_portfolio_impact, currency,
               related_accounts_json, related_holdings_json, related_goals_json,
               source_signals_json, confidence_score, computed_at
        FROM fk_personal_impacts
        ORDER BY computed_at DESC
        LIMIT 20
        """
    ).fetchall()
    cols = ["id", "impact_type", "user_domain", "title", "description", "severity",
            "estimated_monthly_impact", "estimated_portfolio_impact", "currency",
            "related_accounts_json", "related_holdings_json", "related_goals_json",
            "source_signals_json", "confidence_score", "computed_at"]
    result = []
    for r in rows:
        d = dict(zip(cols, r))
        d["related_accounts"] = json.loads(d.pop("related_accounts_json") or "[]")
        d["related_holdings"] = json.loads(d.pop("related_holdings_json") or "[]")
        d["related_goals"] = json.loads(d.pop("related_goals_json") or "[]")
        d["source_signals"] = json.loads(d.pop("source_signals_json") or "[]")
        result.append(d)
    return result


def save_datasheet(scope: str, datasheet_json: str, quality_score: float) -> None:
    conn = _conn()
    conn.execute(
        """
        INSERT INTO fk_ai_datasheets (id, scope, datasheet_json, quality_score, generated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [_uid(), scope, datasheet_json, quality_score, _now()],
    )


def get_latest_datasheet(scope: str = "daily") -> Optional[dict]:
    conn = _conn()
    row = conn.execute(
        """
        SELECT scope, datasheet_json, quality_score, generated_at
        FROM fk_ai_datasheets
        WHERE scope = ?
        ORDER BY generated_at DESC
        LIMIT 1
        """,
        [scope],
    ).fetchone()
    if row is None:
        return None
    return {"scope": row[0], "datasheet_json": row[1], "quality_score": row[2], "generated_at": row[3]}


def save_knowledge_graph_nodes(nodes: list) -> int:
    conn = _conn()
    count = 0
    for node in nodes:
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO fk_knowledge_graph_nodes
                (id, node_type, label, properties_json, computed_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                [node.id, node.node_type, node.label, json.dumps(node.properties), node.computed_at],
            )
            count += 1
        except Exception as e:
            logger.warning("Error guardando nodo %s: %s", node.id, e)
    return count


def save_knowledge_graph_edges(edges: list) -> int:
    conn = _conn()
    count = 0
    for edge in edges:
        try:
            conn.execute(
                """
                INSERT INTO fk_knowledge_graph_edges
                (id, source_id, target_id, relationship, weight, properties_json, computed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [edge.id, edge.source_id, edge.target_id, edge.relationship,
                 edge.weight, json.dumps(edge.properties), edge.computed_at],
            )
            count += 1
        except Exception as e:
            logger.warning("Error guardando arista %s: %s", edge.id, e)
    return count
