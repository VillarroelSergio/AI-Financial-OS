"""Financial Signal Engine — convierte insights macro/mercado en señales financieras."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import yaml

from app.modules.financial_knowledge._shared import now as _now
from app.modules.financial_knowledge._shared import uid as _uid
from app.modules.financial_knowledge.models import (
    Direction,
    EconomicIndicatorInsight,
    FinancialSignal,
    Severity,
    Trend,
)
from app.modules.market_intelligence.storage import repository as mi_repo

logger = logging.getLogger("financial_knowledge.financial_signal_engine")

_SIGNAL_RULES_PATH = Path(__file__).parent.parent / "rules" / "signal_rules.yaml"
_MACRO_RULES_PATH = Path(__file__).parent.parent / "rules" / "macro_rules.yaml"
_MARKET_RULES_PATH = Path(__file__).parent.parent / "rules" / "market_rules.yaml"


def _load_yaml(path: Path) -> dict:
    if path.exists():
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {}


def _make_signal(
    signal_type: str,
    name: str,
    category: str,
    description: str,
    direction: Direction,
    severity: Severity,
    confidence: float,
    quality: float,
    affected_assets: list[str],
    affected_domains: list[str],
    source_indicators: list[str],
    rule_id: str,
) -> FinancialSignal:
    return FinancialSignal(
        id=_uid(),
        signal_type=signal_type,
        name=name,
        category=category,
        description=description,
        direction=direction,
        severity=severity,
        confidence_score=confidence,
        quality_score=quality,
        computed_at=_now(),
        affected_assets=affected_assets,
        affected_user_domains=affected_domains,
        source_indicators=source_indicators,
        rule_id=rule_id,
    )


def _signals_from_insights(
    insights: list[EconomicIndicatorInsight],
    signal_defs: dict,
    macro_rules: dict,
) -> list[FinancialSignal]:
    signals: list[FinancialSignal] = []

    for insight in insights:
        cat = insight.category
        value = insight.value
        trend = insight.trend

        # ── Inflation signals ──────────────────────────────────────────────
        if cat in ("inflation", "core_inflation"):
            rule = macro_rules.get("inflation_above_target", {})
            target = rule.get("target", 2.0)
            warning = rule.get("warning_threshold", 2.5)
            critical = rule.get("critical_threshold", 5.0)

            if value > target:
                severity = Severity.CRITICAL if value >= critical else (Severity.HIGH if value >= warning * 1.5 else Severity.MEDIUM)
                sdef = signal_defs.get("inflation_above_target", {})
                signals.append(_make_signal(
                    signal_type="inflation_above_target",
                    name="Inflación por encima del objetivo",
                    category="macro",
                    description=f"Inflación {value:.1f}% > objetivo {target:.1f}%",
                    direction=Direction.NEGATIVE,
                    severity=severity,
                    confidence=0.9,
                    quality=insight.quality_score,
                    affected_assets=sdef.get("affected_assets", ["cash", "bonds"]),
                    affected_domains=sdef.get("affected_user_domains", ["cash", "savings"]),
                    source_indicators=[insight.indicator_id],
                    rule_id="inflation_above_target",
                ))

            if trend == Trend.RISING:
                sdef = signal_defs.get("inflation_accelerating", {})
                signals.append(_make_signal(
                    signal_type="inflation_accelerating",
                    name="Inflación acelerándose",
                    category="macro",
                    description="Inflación en tendencia alcista",
                    direction=Direction.NEGATIVE,
                    severity=Severity.MEDIUM,
                    confidence=0.75,
                    quality=insight.quality_score,
                    affected_assets=sdef.get("affected_assets", ["cash", "bonds"]),
                    affected_domains=sdef.get("affected_user_domains", ["cash"]),
                    source_indicators=[insight.indicator_id],
                    rule_id="inflation_accelerating",
                ))
            elif trend == Trend.FALLING:
                sdef = signal_defs.get("inflation_decelerating", {})
                signals.append(_make_signal(
                    signal_type="inflation_decelerating",
                    name="Inflación desacelerándose",
                    category="macro",
                    description="Inflación en tendencia bajista",
                    direction=Direction.POSITIVE,
                    severity=Severity.LOW,
                    confidence=0.75,
                    quality=insight.quality_score,
                    affected_assets=sdef.get("affected_assets", ["bonds", "equities"]),
                    affected_domains=sdef.get("affected_user_domains", ["portfolio"]),
                    source_indicators=[insight.indicator_id],
                    rule_id="inflation_decelerating",
                ))

        # ── Rates signals ──────────────────────────────────────────────────
        elif cat in ("interest_rates", "euribor"):
            rule = macro_rules.get("rates_high", {})
            warning = rule.get("warning_threshold", 3.0)
            critical = rule.get("critical_threshold", 5.0)

            if value >= warning:
                severity = Severity.HIGH if value >= critical else Severity.MEDIUM
                sdef = signal_defs.get("rates_high", {})
                signals.append(_make_signal(
                    signal_type="rates_high",
                    name="Tipos de interés elevados",
                    category="macro",
                    description=f"Tipo al {value:.2f}% — nivel históricamente alto",
                    direction=Direction.MIXED,
                    severity=severity,
                    confidence=0.9,
                    quality=insight.quality_score,
                    affected_assets=sdef.get("affected_assets", ["bonds", "real_estate"]),
                    affected_domains=sdef.get("affected_user_domains", ["mortgage", "loans"]),
                    source_indicators=[insight.indicator_id],
                    rule_id="rates_high",
                ))

            if trend == Trend.RISING:
                sdef = signal_defs.get("rates_rising", {})
                signals.append(_make_signal(
                    signal_type="rates_rising",
                    name="Tipos en ascenso",
                    category="macro",
                    description="Tipos de interés en tendencia alcista",
                    direction=Direction.NEGATIVE,
                    severity=Severity.MEDIUM,
                    confidence=0.8,
                    quality=insight.quality_score,
                    affected_assets=sdef.get("affected_assets", ["bonds", "real_estate"]),
                    affected_domains=sdef.get("affected_user_domains", ["mortgage"]),
                    source_indicators=[insight.indicator_id],
                    rule_id="rates_rising",
                ))
            elif trend == Trend.FALLING:
                sdef = signal_defs.get("rates_falling", {})
                signals.append(_make_signal(
                    signal_type="rates_falling",
                    name="Tipos bajando",
                    category="macro",
                    description="Tipos de interés en tendencia bajista",
                    direction=Direction.POSITIVE,
                    severity=Severity.LOW,
                    confidence=0.8,
                    quality=insight.quality_score,
                    affected_assets=sdef.get("affected_assets", ["bonds", "equities"]),
                    affected_domains=sdef.get("affected_user_domains", ["mortgage", "portfolio"]),
                    source_indicators=[insight.indicator_id],
                    rule_id="rates_falling",
                ))

        # ── Unemployment signals ────────────────────────────────────────────
        elif cat == "unemployment":
            if trend == Trend.RISING:
                sdef = signal_defs.get("employment_weakening", {})
                signals.append(_make_signal(
                    signal_type="employment_weakening",
                    name="Empleo deteriorándose",
                    category="macro",
                    description=f"Desempleo del {value:.1f}% en tendencia alcista",
                    direction=Direction.NEGATIVE,
                    severity=Severity.MEDIUM,
                    confidence=0.7,
                    quality=insight.quality_score,
                    affected_assets=sdef.get("affected_assets", ["equities"]),
                    affected_domains=sdef.get("affected_user_domains", ["income"]),
                    source_indicators=[insight.indicator_id],
                    rule_id="unemployment_rising",
                ))

    return signals


def _signals_from_market(
    quotes: list[dict],
    forex: list[dict],
    bonds: list[dict],
    signal_defs: dict,
    market_rules: dict,
) -> list[FinancialSignal]:
    signals: list[FinancialSignal] = []

    # ── Equity signals ──────────────────────────────────────────────────────
    equity_threshold = market_rules.get("equity_drawdown", {}).get("drawdown_threshold", -5.0)
    equity_types = {"equity_index", "etf_equity"}
    for q in quotes:
        if q.get("asset_type") not in equity_types:
            continue
        chg = q.get("change_pct", 0.0) or 0.0
        if chg <= equity_threshold:
            sdef = signal_defs.get("equity_market_drawdown", {})
            signals.append(_make_signal(
                signal_type="equity_market_drawdown",
                name="Caída en renta variable",
                category="market",
                description=f"{q.get('catalog_item_id', '?')}: {chg:.1f}%",
                direction=Direction.NEGATIVE,
                severity=Severity.HIGH if chg <= -15 else Severity.MEDIUM,
                confidence=0.85,
                quality=float(q.get("quality_score", 1.0)),
                affected_assets=sdef.get("affected_assets", ["equities"]),
                affected_domains=sdef.get("affected_user_domains", ["portfolio"]),
                source_indicators=[q.get("catalog_item_id", "")],
                rule_id="equity_drawdown",
            ))
        elif chg > 0:
            sdef = signal_defs.get("equity_market_positive", {})
            signals.append(_make_signal(
                signal_type="equity_market_positive",
                name="Renta variable en positivo",
                category="market",
                description=f"{q.get('catalog_item_id', '?')}: +{chg:.1f}%",
                direction=Direction.POSITIVE,
                severity=Severity.LOW,
                confidence=0.8,
                quality=float(q.get("quality_score", 1.0)),
                affected_assets=sdef.get("affected_assets", ["equities"]),
                affected_domains=sdef.get("affected_user_domains", ["portfolio"]),
                source_indicators=[q.get("catalog_item_id", "")],
                rule_id="equity_drawdown",
            ))

    # ── Oil / Energy signals ────────────────────────────────────────────────
    oil_threshold = market_rules.get("oil_spike", {}).get("change_pct_threshold", 10.0)
    elec_threshold = market_rules.get("electricity_price_spike", {}).get("change_pct_threshold", 20.0)
    for q in quotes:
        cid = q.get("catalog_item_id", "")
        chg = q.get("change_pct", 0.0) or 0.0
        if "oil" in cid and chg >= oil_threshold:
            sdef = signal_defs.get("oil_spike", {})
            signals.append(_make_signal(
                signal_type="oil_spike",
                name="Subida brusca del petróleo",
                category="commodities",
                description=f"Petróleo sube +{chg:.1f}%",
                direction=Direction.NEGATIVE,
                severity=Severity.HIGH,
                confidence=0.85,
                quality=float(q.get("quality_score", 1.0)),
                affected_assets=sdef.get("affected_assets", ["commodities"]),
                affected_domains=sdef.get("affected_user_domains", ["expenses"]),
                source_indicators=[cid],
                rule_id="oil_spike",
            ))
        if "electricity" in cid and chg >= elec_threshold:
            sdef = signal_defs.get("electricity_price_spike", {})
            signals.append(_make_signal(
                signal_type="electricity_price_spike",
                name="Subida del precio de la electricidad",
                category="commodities",
                description=f"Electricidad sube +{chg:.1f}%",
                direction=Direction.NEGATIVE,
                severity=Severity.MEDIUM,
                confidence=0.8,
                quality=float(q.get("quality_score", 1.0)),
                affected_assets=sdef.get("affected_assets", ["commodities"]),
                affected_domains=sdef.get("affected_user_domains", ["expenses", "energy"]),
                source_indicators=[cid],
                rule_id="electricity_price_spike",
            ))

    # ── Crypto signals ──────────────────────────────────────────────────────
    crypto_threshold = market_rules.get("crypto_volatility_high", {}).get("change_pct_threshold", 15.0)
    for q in quotes:
        if q.get("asset_type") != "crypto":
            continue
        chg = abs(q.get("change_pct", 0.0) or 0.0)
        if chg >= crypto_threshold:
            sdef = signal_defs.get("crypto_volatility_high", {})
            signals.append(_make_signal(
                signal_type="crypto_volatility_high",
                name="Alta volatilidad en cripto",
                category="market",
                description=f"{q.get('catalog_item_id', '?')}: {chg:.1f}% de cambio",
                direction=Direction.MIXED,
                severity=Severity.MEDIUM,
                confidence=0.8,
                quality=float(q.get("quality_score", 1.0)),
                affected_assets=sdef.get("affected_assets", ["crypto"]),
                affected_domains=sdef.get("affected_user_domains", ["portfolio"]),
                source_indicators=[q.get("catalog_item_id", "")],
                rule_id="crypto_volatility_high",
            ))

    # ── Forex signals ───────────────────────────────────────────────────────
    market_rules.get("usd_strength", {}).get("change_pct_threshold", -2.0)
    for fx in forex:
        if fx.get("base_currency") == "EUR" and fx.get("quote_currency") == "USD":
            rate = fx.get("rate", 1.0) or 1.0
            # Calcular cambio aproximado (sin histórico: marcar como señal si rate < 1.05)
            if rate < 1.05:
                for stype, sname, direction, rule in [
                    ("eur_weakness", "Euro débil frente al dólar", Direction.NEGATIVE, "eur_weakness"),
                    ("usd_strength", "Dólar fuerte", Direction.MIXED, "usd_strength"),
                ]:
                    sdef = signal_defs.get(stype, {})
                    signals.append(_make_signal(
                        signal_type=stype,
                        name=sname,
                        category="forex",
                        description=f"EUR/USD = {rate:.4f}",
                        direction=direction,
                        severity=Severity.LOW,
                        confidence=0.7,
                        quality=float(fx.get("quality_score", 1.0)),
                        affected_assets=sdef.get("affected_assets", ["forex"]),
                        affected_domains=sdef.get("affected_user_domains", ["portfolio"]),
                        source_indicators=["eur_usd"],
                        rule_id=rule,
                    ))

    # ── Yield curve signals ─────────────────────────────────────────────────
    bond_map: dict[tuple, float] = {}
    for b in bonds:
        key = (b.get("country", ""), b.get("maturity", ""))
        bond_map[key] = b.get("yield_value", 0.0) or 0.0

    for country in set(k[0] for k in bond_map):
        y2 = bond_map.get((country, "2Y"), 0.0)
        y10 = bond_map.get((country, "10Y"), 0.0)
        if y2 > 0 and y10 > 0 and y2 > y10:
            sdef = signal_defs.get("yield_curve_inverted", {})
            signals.append(_make_signal(
                signal_type="yield_curve_inverted",
                name="Curva de tipos invertida",
                category="macro",
                description=f"{country}: 2Y={y2:.2f}% > 10Y={y10:.2f}% — señal de recesión",
                direction=Direction.NEGATIVE,
                severity=Severity.HIGH,
                confidence=0.85,
                quality=0.9,
                affected_assets=sdef.get("affected_assets", ["bonds", "equities"]),
                affected_domains=sdef.get("affected_user_domains", ["portfolio"]),
                source_indicators=[f"bond_{country.lower()}_2y", f"bond_{country.lower()}_10y"],
                rule_id="yield_curve_inverted",
            ))

    return signals


def compute_signals(
    insights: Optional[list[EconomicIndicatorInsight]] = None,
    quotes: Optional[list[dict]] = None,
    forex: Optional[list[dict]] = None,
    bonds: Optional[list[dict]] = None,
) -> list[FinancialSignal]:
    """Genera señales financieras desde insights macro y datos de mercado."""
    signal_defs = _load_yaml(_SIGNAL_RULES_PATH)
    macro_rules = _load_yaml(_MACRO_RULES_PATH)
    market_rules = _load_yaml(_MARKET_RULES_PATH)

    if insights is None:
        insights = []
    if quotes is None:
        quotes = mi_repo.get_latest_quotes()
    if forex is None:
        forex = mi_repo.get_latest_forex()
    if bonds is None:
        bonds = mi_repo.get_latest_bonds()

    signals: list[FinancialSignal] = []
    signals.extend(_signals_from_insights(insights, signal_defs, macro_rules))
    signals.extend(_signals_from_market(quotes, forex, bonds, signal_defs, market_rules))

    # Deduplicar por signal_type (mantener el de mayor confianza)
    seen: dict[str, FinancialSignal] = {}
    for sig in signals:
        existing = seen.get(sig.signal_type)
        if existing is None or sig.confidence_score > existing.confidence_score:
            seen[sig.signal_type] = sig

    result = list(seen.values())
    logger.info("FinancialSignalEngine: %d señales generadas", len(result))
    return result
