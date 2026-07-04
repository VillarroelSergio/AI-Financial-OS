"""Knowledge Graph Engine — construye grafo de conocimiento financiero."""
from __future__ import annotations
import logging

from app.modules.financial_knowledge._shared import uid as _uid, now as _now
from app.modules.financial_knowledge.models import (
    EconomicIndicatorInsight, FinancialSignal, MarketRegime,
    PersonalImpact, KnowledgeGraphNode, KnowledgeGraphEdge,
)

logger = logging.getLogger("financial_knowledge.knowledge_graph_engine")


def _node(node_type: str, label: str, props: dict | None = None) -> KnowledgeGraphNode:
    return KnowledgeGraphNode(
        id=f"{node_type}:{label.lower().replace(' ', '_')}",
        node_type=node_type,
        label=label,
        computed_at=_now(),
        properties=props or {},
    )


def _edge(source_id: str, target_id: str, relationship: str, weight: float = 1.0) -> KnowledgeGraphEdge:
    return KnowledgeGraphEdge(
        id=_uid(),
        source_id=source_id,
        target_id=target_id,
        relationship=relationship,
        weight=weight,
        computed_at=_now(),
    )


def build_knowledge_graph(
    insights: list[EconomicIndicatorInsight],
    signals: list[FinancialSignal],
    regime: MarketRegime | None,
    impacts: list[PersonalImpact],
) -> tuple[list[KnowledgeGraphNode], list[KnowledgeGraphEdge]]:
    """Construye nodos y aristas del grafo de conocimiento."""
    nodes: list[KnowledgeGraphNode] = []
    edges: list[KnowledgeGraphEdge] = []
    node_ids: set[str] = set()

    def add_node(n: KnowledgeGraphNode) -> None:
        if n.id not in node_ids:
            nodes.append(n)
            node_ids.add(n.id)

    # ── Nodos de régimen ─────────────────────────────────────────────────────
    if regime:
        regime_node = _node("regime", regime.risk_level.value, {
            "inflation": regime.inflation_regime.value,
            "rates": regime.rates_regime.value,
            "growth": regime.growth_regime.value,
            "trend": regime.market_trend.value,
            "confidence": regime.confidence_score,
        })
        add_node(regime_node)

    # ── Nodos de indicadores ─────────────────────────────────────────────────
    for insight in insights:
        n = _node("indicator", insight.name, {
            "value": insight.value,
            "trend": insight.trend.value,
            "severity": insight.severity.value,
            "country": insight.country,
        })
        add_node(n)

    # ── Nodos de señales y relaciones ─────────────────────────────────────────
    for signal in signals:
        sig_node = _node("signal", signal.signal_type, {
            "severity": signal.severity.value,
            "direction": signal.direction.value,
            "confidence": signal.confidence_score,
        })
        add_node(sig_node)

        # Señal ← derived_from → indicadores fuente
        for src_id in signal.source_indicators:
            indicator_node_id = f"indicator:{src_id.lower().replace(' ', '_')}"
            if indicator_node_id in node_ids:
                edges.append(_edge(indicator_node_id, sig_node.id, "derived_from", signal.confidence_score))

        # Señal → affects → activos
        for asset in signal.affected_assets:
            asset_node = _node("asset", asset)
            add_node(asset_node)
            edges.append(_edge(sig_node.id, asset_node.id, "affects", 0.8))

        # Señal → influences → régimen
        if regime:
            regime_node_id = f"regime:{regime.risk_level.value}"
            edges.append(_edge(sig_node.id, regime_node_id, "influences", signal.confidence_score))

    # ── Nodos de impacto personal ─────────────────────────────────────────────
    for impact in impacts:
        impact_node = _node("personal_impact", impact.impact_type, {
            "severity": impact.severity.value,
            "domain": impact.user_domain,
        })
        add_node(impact_node)

        # Señales fuente → causa impacto personal
        for sig_id in impact.source_signals:
            # Buscar el signal_type correspondiente
            matching = [s for s in signals if s.id == sig_id]
            if matching:
                sig_node_id = f"signal:{matching[0].signal_type}"
                edges.append(_edge(sig_node_id, impact_node.id, "causes_impact", impact.confidence_score))

    logger.info(
        "KnowledgeGraphEngine: %d nodos, %d aristas generados",
        len(nodes), len(edges),
    )
    return nodes, edges
