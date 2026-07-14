"""AI-3 — Centro de Análisis: capa proactiva determinista.

Flujo (06_AI_STRATEGY, restricción innegociable): un trigger determinista arma un
bundle de CIFRAS CERRADAS reutilizando servicios existentes (nunca segunda fuente
de verdad), y el LLM sólo lo NARRA en una única llamada sin tools. Si el LLM falla,
el brief se persiste igual con `narrative=None` y el frontend pinta el bundle tal
cual. La IA es mejora progresiva, no dependencia.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai import AiBrief
from app.modules.ai.action_whitelist import is_allowed_action
from app.modules.ai.prompts.guardrails import enforce_advice_guardrail, sanitize_response
from app.modules.ai.prompts.system_prompt import get_system_prompt
from app.modules.insights import service as insights_service

logger = logging.getLogger(__name__)


# ── Orchestrator (determinista) ────────────────────────────────────────────────

def _monthly_review_bundle(db: Session, period: str) -> dict[str, Any]:
    """Bundle del scope monthly_review. Reutiliza `get_monthly_review`, que ya calcula
    ingresos/gastos/ahorro/tasa + señales del Insights Engine de forma determinista."""
    review = insights_service.get_monthly_review(db, period)

    signals = [*review.top_warnings, *review.top_positive, *review.top_changes]
    # Acciones enlazables deduplicadas (whitelist: vienen de InsightActionOut, no del LLM).
    actions: list[dict[str, Any]] = []
    seen_actions: set[str] = set()
    for ins in signals:
        for act in ins.actions:
            if not is_allowed_action(act.target):  # AI-4: descarta rutas desconocidas
                continue
            key = f"{act.target}:{json.dumps(act.params, sort_keys=True)}"
            if key not in seen_actions:
                seen_actions.add(key)
                actions.append({"label": act.label, "target": act.target, "params": act.params})

    return {
        "scope": "monthly_review",
        "period": review.period,
        "headline": review.headline,
        "summary": review.summary,
        "data_state": review.data_status.value,
        "key_figures": [
            {"label": "Ingresos", "value": review.income, "unit": "EUR"},
            {"label": "Gastos", "value": review.expenses, "unit": "EUR"},
            {"label": "Ahorro", "value": review.savings, "unit": "EUR"},
            {"label": "Tasa de ahorro", "value": review.savings_rate, "unit": "%"},
        ],
        "signals": [
            {
                "title": i.title,
                "summary": i.summary,
                "severity": i.severity.value,
                "type": i.type.value,
            }
            for i in signals
        ],
        "actions": actions,
        "sources": [s.model_dump() for s in review.sources],
    }


# scope → builder. Añadir weekly_brief/portfolio_health/budget_pulse aquí cuando toque.
# ponytail: sólo monthly_review en V1 (D2: mensual primero, se apoya en snapshots reales).
SCOPES: dict[str, Callable[[Session, str], dict[str, Any]]] = {
    "monthly_review": _monthly_review_bundle,
}


def _current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def build_bundle(db: Session, scope: str, period: str | None = None) -> dict[str, Any]:
    if scope not in SCOPES:
        raise ValueError(f"Scope desconocido: {scope}. Disponibles: {list(SCOPES)}")
    if period and (len(period) != 7 or "-" not in period):
        raise ValueError("period debe ser YYYY-MM")
    return SCOPES[scope](db, period or _current_period())


# ── Redacción (LLM como narrador del bundle) ───────────────────────────────────

def _deterministic_narrative(bundle: dict[str, Any]) -> str:
    """Fallback sin LLM: narrativa mínima a partir del bundle. Nunca falla."""
    lines = [bundle["headline"], "", bundle["summary"]]
    signals = bundle.get("signals") or []
    if signals:
        lines += ["", "Señales a revisar:"]
        lines += [f"- {s['title']}: {s['summary']}" for s in signals]
    return "\n".join(lines)


def _redaction_messages(bundle: dict[str, Any]) -> list[dict[str, str]]:
    instruction = (
        "Eres el redactor del Centro de Análisis. Narra en prosa clara el siguiente "
        "informe financiero ya calculado. NO recalcules ni inventes cifras: usa sólo las "
        "que aparecen en el bundle. Sigue el contrato de salida (sin tablas, sin emojis, "
        "sin separadores). Estructura: qué ocurre, por qué importa y qué opciones hay. "
        "Si data_state no es 'complete', dilo con honestidad en vez de rellenar.\n\n"
        f"Bundle (cifras cerradas):\n{json.dumps(bundle, ensure_ascii=False, default=str)}"
    )
    return [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": instruction},
    ]


async def render_narrative(
    bundle: dict[str, Any],
    provider_name: str | None,
    model: str | None,
) -> tuple[str | None, str | None, str | None]:
    """Una sola llamada LLM sin tools. Devuelve (narrative, provider, model) o
    (None, None, None) si el provider no está disponible — el caller hace fallback."""
    from app.modules.ai.service import get_provider  # local: evita ciclo de import

    provider = get_provider(provider_name)
    try:
        response = await provider.chat(
            messages=_redaction_messages(bundle),
            tools=None,
            model=model,
            max_tokens=settings.AI_MAX_OUTPUT_TOKENS,
        )
    except (httpx.TimeoutException, httpx.TransportError) as exc:
        logger.warning("Brief LLM redaction failed (%s) — usando fallback determinista", exc)
        return None, None, None
    narrative = enforce_advice_guardrail(sanitize_response(response.content))
    if not narrative:
        return None, None, None
    return narrative, provider.name, (model or settings.AI_DEFAULT_MODEL)


# ── Persistencia (idempotente por scope+period, DELETE+INSERT) ─────────────────

def _serialize(brief: AiBrief) -> dict[str, Any]:
    return {
        "id": brief.id,
        "scope": brief.scope,
        "period": brief.period,
        "bundle": json.loads(brief.bundle_json),
        "narrative": brief.narrative,
        "data_state": brief.data_state,
        "provider": brief.provider,
        "model": brief.model,
        "created_at": brief.created_at.isoformat() if brief.created_at else None,
    }


def get_brief(db: Session, scope: str, period: str) -> dict[str, Any] | None:
    brief = (
        db.query(AiBrief)
        .filter(AiBrief.scope == scope, AiBrief.period == period)
        .first()
    )
    return _serialize(brief) if brief else None


def list_briefs(db: Session, limit: int = 20) -> list[dict[str, Any]]:
    briefs = db.query(AiBrief).order_by(AiBrief.created_at.desc()).limit(limit).all()
    return [_serialize(b) for b in briefs]


async def generate_brief(
    db: Session,
    scope: str,
    period: str | None = None,
    provider_name: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    if not settings.AI_ASSISTANT_ENABLED:
        raise RuntimeError("AI Assistant is disabled (AI_ASSISTANT_ENABLED=false)")

    bundle = build_bundle(db, scope, period)
    resolved_period = bundle["period"]

    narrative, used_provider, used_model = await render_narrative(bundle, provider_name, model)
    if narrative is None:
        narrative = _deterministic_narrative(bundle)  # fallback: el brief nunca bloquea

    # Idempotente: un único brief por (scope, period).
    db.query(AiBrief).filter(
        AiBrief.scope == scope, AiBrief.period == resolved_period
    ).delete()
    brief = AiBrief(
        scope=scope,
        period=resolved_period,
        bundle_json=json.dumps(bundle, ensure_ascii=False, default=str),
        narrative=narrative,
        data_state=bundle["data_state"],
        provider=used_provider,
        model=used_model,
    )
    db.add(brief)
    db.commit()
    db.refresh(brief)
    return _serialize(brief)
