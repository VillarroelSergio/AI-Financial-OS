"""Personal Impact Engine — cuantifica el impacto personal de señales financieras."""
from __future__ import annotations
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import yaml

from sqlalchemy.orm import Session

from app.modules.financial_knowledge.models import FinancialSignal, PersonalImpact, Severity

logger = logging.getLogger("financial_knowledge.personal_impact_engine")

_RULES_PATH = Path(__file__).parent.parent / "rules" / "personal_impact_rules.yaml"


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _load_rules() -> dict:
    if _RULES_PATH.exists():
        return yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8")) or {}
    return {}


def _active_types(signals: list[FinancialSignal]) -> dict[str, FinancialSignal]:
    return {s.signal_type: s for s in signals}


def _get_user_cash_total(db: Session) -> float:
    """Suma saldos de cuentas de tipo efectivo/ahorro."""
    try:
        from app.models.account import Account
        rows = db.query(Account).filter(Account.is_active == True).all()
        return sum(
            getattr(a, "balance", 0.0) or 0.0
            for a in rows
            if getattr(a, "account_type", "") in ("checking", "savings", "cash")
        )
    except Exception:
        return 0.0


def _get_user_portfolio_value(db: Session) -> float:
    """Valor total de la cartera de inversión."""
    try:
        from app.models.investment import Investment
        rows = db.query(Investment).filter(Investment.is_active == True).all()
        return sum(getattr(r, "current_value", 0.0) or 0.0 for r in rows)
    except Exception:
        return 0.0


def _get_user_goals(db: Session) -> list[dict]:
    try:
        from app.models.goal import Goal
        rows = db.query(Goal).filter(Goal.is_active == True).all()
        return [{"id": str(g.id), "name": getattr(g, "name", ""), "target": getattr(g, "target_amount", 0.0)} for g in rows]
    except Exception:
        return []


def _get_user_account_ids(db: Session) -> list[str]:
    try:
        from app.models.account import Account
        rows = db.query(Account).filter(Account.is_active == True).all()
        return [str(r.id) for r in rows]
    except Exception:
        return []


def compute_personal_impacts(
    signals: list[FinancialSignal],
    db: Optional[Session] = None,
) -> list[PersonalImpact]:
    """Genera impactos personales desde señales activas y datos del usuario."""
    rules = _load_rules()
    active = _active_types(signals)
    impacts: list[PersonalImpact] = []
    now = _now()

    # ── Cash drag ────────────────────────────────────────────────────────────
    if "inflation_above_target" in active:
        sig = active["inflation_above_target"]
        cash_total = _get_user_cash_total(db) if db else 0.0
        # Estimación: inflación del 3% sobre saldo en efectivo → pérdida mensual
        inflation_estimate = 0.03  # fallback conservador
        monthly_drag = cash_total * (inflation_estimate / 12) if cash_total > 0 else None

        impacts.append(PersonalImpact(
            id=_uid(),
            impact_type="cash_drag",
            user_domain="cash",
            title="Erosión del efectivo por inflación",
            description=(
                f"La inflación por encima del objetivo erosiona el poder adquisitivo "
                f"de tu efectivo{f' ({cash_total:,.0f} €)' if cash_total > 0 else ''}."
            ),
            severity=sig.severity,
            confidence_score=sig.confidence_score * 0.85,
            computed_at=now,
            estimated_monthly_impact=monthly_drag,
            currency="EUR",
            source_signals=[sig.id],
        ))

    # ── Mortgage pressure ────────────────────────────────────────────────────
    if "rates_high" in active or "rates_rising" in active:
        sig = active.get("rates_high") or active.get("rates_rising")
        impacts.append(PersonalImpact(
            id=_uid(),
            impact_type="mortgage_pressure",
            user_domain="mortgage",
            title="Presión en hipotecas variables",
            description=(
                "Los tipos de interés elevados o en ascenso incrementan el coste "
                "de las hipotecas a tipo variable referenciadas al Euríbor."
            ),
            severity=sig.severity,
            confidence_score=sig.confidence_score * 0.8,
            computed_at=now,
            currency="EUR",
            source_signals=[sig.id],
        ))

    # ── FX exposure ──────────────────────────────────────────────────────────
    if "eur_weakness" in active or "usd_strength" in active:
        sig = active.get("eur_weakness") or active.get("usd_strength")
        portfolio_value = _get_user_portfolio_value(db) if db else 0.0
        impacts.append(PersonalImpact(
            id=_uid(),
            impact_type="fx_exposure_loss",
            user_domain="portfolio",
            title="Impacto divisa: Euro débil",
            description=(
                "La debilidad del euro frente al dólar puede afectar el valor "
                "de los activos internacionales denominados en USD al convertirlos a EUR, "
                "aunque también puede suponer una ganancia si tienes exposición neta a USD."
            ),
            severity=Severity.LOW,
            confidence_score=0.6,
            computed_at=now,
            currency="EUR",
            source_signals=[sig.id],
        ))

    # ── Equity drawdown impact ────────────────────────────────────────────────
    if "equity_market_drawdown" in active:
        sig = active["equity_market_drawdown"]
        portfolio_value = _get_user_portfolio_value(db) if db else 0.0
        estimated_loss = portfolio_value * 0.05 if portfolio_value > 0 else None
        goals = _get_user_goals(db) if db else []
        goal_ids = [g["id"] for g in goals]

        impacts.append(PersonalImpact(
            id=_uid(),
            impact_type="equity_drawdown_impact",
            user_domain="portfolio",
            title="Caída de mercado impacta tu cartera",
            description=(
                f"Las caídas en renta variable afectan directamente el valor de tu cartera"
                f"{f' (valor estimado: {portfolio_value:,.0f} €)' if portfolio_value > 0 else ''}."
            ),
            severity=sig.severity,
            confidence_score=sig.confidence_score * 0.9,
            computed_at=now,
            estimated_portfolio_impact=estimated_loss,
            currency="EUR",
            related_goals=goal_ids[:3],
            source_signals=[sig.id],
        ))

    # ── Energy cost pressure ──────────────────────────────────────────────────
    if "electricity_price_spike" in active or "oil_spike" in active:
        sig = active.get("electricity_price_spike") or active.get("oil_spike")
        impacts.append(PersonalImpact(
            id=_uid(),
            impact_type="energy_cost_pressure",
            user_domain="expenses",
            title="Presión en gastos energéticos",
            description=(
                "La subida del precio de la electricidad o el petróleo puede incrementar "
                "tus gastos mensuales en energía y transporte."
            ),
            severity=Severity.LOW,
            confidence_score=0.65,
            computed_at=now,
            currency="EUR",
            source_signals=[sig.id],
        ))

    # ── Goal delay risk ───────────────────────────────────────────────────────
    if "equity_market_drawdown" in active and "inflation_above_target" in active:
        goals = _get_user_goals(db) if db else []
        if goals:
            goal_ids = [g["id"] for g in goals[:3]]
            impacts.append(PersonalImpact(
                id=_uid(),
                impact_type="goal_delay_risk",
                user_domain="goals",
                title="Riesgo de retraso en objetivos financieros",
                description=(
                    "La combinación de caídas de mercado e inflación alta puede reducir "
                    "el valor de tus activos y retrasar la consecución de tus metas financieras."
                ),
                severity=Severity.MEDIUM,
                confidence_score=0.6,
                computed_at=now,
                currency="EUR",
                related_goals=goal_ids,
                source_signals=[active["equity_market_drawdown"].id, active["inflation_above_target"].id],
            ))

    logger.info("PersonalImpactEngine: %d impactos generados", len(impacts))
    return impacts
