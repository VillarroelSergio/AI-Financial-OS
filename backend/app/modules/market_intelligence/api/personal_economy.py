"""Economía personal — cruce determinista entre macro (DuckDB) y tus finanzas (SQLite).

Responde a "¿y esto qué significa para mí en euros?": inflación personal vs IPC,
salario real, coste/oportunidad de la liquidez, Euríbor para la hipoteca,
calendario fiscal español y noticias relevantes para el perfil del usuario.
Sin LLM: todo cuantificado desde datos ya ingeridos.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.category import Category
from app.models.investment import Holding, InvestmentAsset
from app.models.transaction import Transaction
from app.modules.market_intelligence.storage import repository


def _month_shift(day: date, months: int) -> str:
    """Prefijo YYYY-MM desplazado N meses hacia atrás."""
    total = day.year * 12 + (day.month - 1) - months
    return f"{total // 12}-{total % 12 + 1:02d}"


def _macro_series(catalog_id: str) -> list[tuple[str, float]]:
    try:
        return repository.get_macro_history(max_points=30).get(catalog_id, [])
    except Exception:
        return []


def _latest_and_year_ago(catalog_id: str) -> tuple[float | None, float | None]:
    points = _macro_series(catalog_id)
    if not points:
        return None, None
    latest_period, latest_value = points[-1]
    year_ago = None
    # Los periodos de DuckDB pueden venir malformados ("2021-", fechas sueltas…):
    # sin un YYYY-MM válido devolvemos solo el último valor, nunca un 500.
    match = re.match(r"(\d{4})-(\d{2})", str(latest_period))
    if match:
        target = f"{int(match.group(1)) - 1}-{match.group(2)}"
        for period, value in points:
            if str(period)[:7] <= target:
                year_ago = value
    return latest_value, year_ago


# ──────────────────────────────────────────────────────────────
# Inflación personal: gasto de los últimos 12 meses vs los 12 anteriores
# ──────────────────────────────────────────────────────────────

def _personal_inflation(db: Session, ipc: float | None, ipc_core: float | None) -> dict:
    today = date.today()
    current_from = f"{_month_shift(today, 12)}-01"
    previous_from = f"{_month_shift(today, 24)}-01"
    txs = (
        db.query(Transaction.date, Transaction.amount, Category.name)
        .join(Category, Transaction.category_id == Category.id, isouter=True)
        .filter(
            Transaction.type == "expense",
            Transaction.analytics_scope == "personal",
            Transaction.date >= previous_from,
        )
        .all()
    )
    current_total, previous_total = 0.0, 0.0
    by_cat: dict[str, list[float]] = {}
    for tx_date, amount, cat_name in txs:
        value = abs(float(amount))
        bucket = 0 if str(tx_date) >= current_from else 1
        name = cat_name or "Sin categoría"
        pair = by_cat.setdefault(name, [0.0, 0.0])
        pair[bucket] += value
        if bucket == 0:
            current_total += value
        else:
            previous_total += value

    def _yoy(current: float, previous: float) -> float | None:
        return round((current - previous) / previous * 100, 1) if previous > 0 else None

    categories = [
        {
            "category": name,
            "current": round(pair[0], 2),
            "previous": round(pair[1], 2),
            "yoy_pct": _yoy(pair[0], pair[1]),
        }
        for name, pair in sorted(by_cat.items(), key=lambda kv: kv[1][0], reverse=True)
        if pair[0] > 0 or pair[1] > 0
    ][:8]
    return {
        "user_yoy_pct": _yoy(current_total, previous_total),
        "ipc_general": ipc,
        "ipc_subyacente": ipc_core,
        "current_total": round(current_total, 2),
        "previous_total": round(previous_total, 2),
        "by_category": categories,
    }


# ──────────────────────────────────────────────────────────────
# Salario real: nómina media reciente vs hace un año, deflactada por IPC
# ──────────────────────────────────────────────────────────────

def _real_salary(db: Session, ipc: float | None) -> dict:
    today = date.today()

    def _avg_salary(months_back_from: int) -> float | None:
        """Media mensual de ingresos de salario en una ventana de 3 meses."""
        frm = f"{_month_shift(today, months_back_from)}-01"
        to = f"{_month_shift(today, months_back_from - 3)}-01"
        rows = (
            db.query(func.sum(Transaction.amount))
            .join(Category, Transaction.category_id == Category.id, isouter=True)
            .filter(
                Transaction.type == "income",
                Transaction.analytics_scope == "personal",
                Transaction.date >= frm,
                Transaction.date < to,
                func.lower(func.coalesce(Category.name, "")).contains("salario"),
            )
            .scalar()
        )
        total = float(rows or 0)
        return round(total / 3, 2) if total > 0 else None

    current = _avg_salary(3)
    year_ago = _avg_salary(15)
    nominal = (
        round((current - year_ago) / year_ago * 100, 1)
        if current is not None and year_ago is not None and year_ago > 0
        else None
    )
    real = round(nominal - ipc, 1) if nominal is not None and ipc is not None else None
    return {
        "monthly_now": current,
        "monthly_year_ago": year_ago,
        "nominal_yoy_pct": nominal,
        "ipc": ipc,
        "real_yoy_pct": real,
    }


# ──────────────────────────────────────────────────────────────
# Liquidez y remuneración del ahorro
# ──────────────────────────────────────────────────────────────

def _savings(db: Session, tipo_bce: float | None) -> dict:
    liquidity = float(
        db.query(func.sum(Account.current_balance))
        .filter(Account.is_active == True, Account.type.in_(["cash", "bank"]))  # noqa: E712
        .scalar()
        or 0
    )
    potential = round(liquidity * tipo_bce / 100 / 12, 2) if tipo_bce is not None and liquidity > 0 else None
    return {
        "idle_liquidity": round(liquidity, 2),
        "tipo_bce": tipo_bce,
        "potential_monthly": potential,
    }


# ──────────────────────────────────────────────────────────────
# Calendario fiscal español (fechas recurrentes, deterministas)
# ──────────────────────────────────────────────────────────────

_FISCAL_MILESTONES: list[tuple[int, int, str, str]] = [
    (1, 20, "Modelo 111/115 y 303 — 4T año anterior (autónomos)", "autonomos"),
    (1, 31, "Modelo 390 — resumen anual de IVA", "autonomos"),
    (4, 2, "Inicio de la campaña de la Renta", "todos"),
    (4, 21, "Modelo 303 — IVA 1T (autónomos)", "autonomos"),
    (6, 25, "Fecha límite Renta con resultado a ingresar y domiciliación", "todos"),
    (6, 30, "Fin de la campaña de la Renta", "todos"),
    (7, 21, "Modelo 303 — IVA 2T (autónomos)", "autonomos"),
    (10, 20, "Modelo 303 — IVA 3T (autónomos)", "autonomos"),
    (12, 31, "Último día para aportar al plan de pensiones (deducción IRPF)", "todos"),
]


def _fiscal_calendar(limit: int = 5) -> list[dict]:
    today = date.today()
    upcoming = []
    for year in (today.year, today.year + 1):
        for month, day, label, audience in _FISCAL_MILESTONES:
            milestone = date(year, month, day)
            if milestone >= today:
                upcoming.append(
                    {
                        "date": milestone.isoformat(),
                        "label": label,
                        "audience": audience,
                        "days_left": (milestone - today).days,
                    }
                )
    upcoming.sort(key=lambda m: m["date"])
    return upcoming[:limit]


# ──────────────────────────────────────────────────────────────
# Noticias relevantes para el perfil del usuario
# ──────────────────────────────────────────────────────────────

_BASE_KEYWORDS = ["euribor", "hipoteca", "ipc", "inflacion", "bce", "vivienda", "salario", "smi", "irpf"]


def _strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in text if not unicodedata.combining(c))


def _relevant_news(db: Session, limit: int = 6) -> list[dict]:
    keywords = list(_BASE_KEYWORDS)
    assets = (
        db.query(InvestmentAsset.name, InvestmentAsset.ticker)
        .join(Holding, Holding.asset_id == InvestmentAsset.id)
        .all()
    )
    for name, ticker in assets:
        if name and len(name) >= 4:
            keywords.append(_strip_accents(name))
        if ticker and len(ticker) >= 3:
            keywords.append(_strip_accents(ticker))
    try:
        rows = repository.get_latest_news(limit=80)
    except Exception:
        return []
    scored = []
    for row in rows:
        title = _strip_accents(str(row.get("title") or ""))
        hits = [k for k in keywords if k in title]
        if hits:
            scored.append((len(hits), row, hits))
    scored.sort(key=lambda s: str(s[1].get("published_at") or ""), reverse=True)
    scored.sort(key=lambda s: s[0], reverse=True)
    return [
        {
            "id": row["id"],
            "title": row.get("title"),
            "published_at": str(row.get("published_at") or ""),
            "source_name": row.get("source_name"),
            "url": row.get("url"),
            "matched": hits,
        }
        for _, row, hits in scored[:limit]
    ]


# ──────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────

def compute_personal_economy(db: Session) -> dict:
    def _safe(fn, fallback):
        """Un bloque con datos sucios nunca debe tumbar el endpoint entero."""
        try:
            return fn()
        except Exception:
            return fallback

    ipc, _ = _safe(lambda: _latest_and_year_ago("ipc_general"), (None, None))
    ipc_core, _ = _safe(lambda: _latest_and_year_ago("ipc_subyacente"), (None, None))
    euribor, euribor_year_ago = _safe(lambda: _latest_and_year_ago("euribor_12m"), (None, None))
    tipo_bce, _ = _safe(lambda: _latest_and_year_ago("tipo_bce"), (None, None))

    empty_inflation = {
        "user_yoy_pct": None, "ipc_general": ipc, "ipc_subyacente": ipc_core,
        "current_total": 0.0, "previous_total": 0.0, "by_category": [],
    }
    empty_salary = {
        "monthly_now": None, "monthly_year_ago": None,
        "nominal_yoy_pct": None, "ipc": ipc, "real_yoy_pct": None,
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "personal_inflation": _safe(lambda: _personal_inflation(db, ipc, ipc_core), empty_inflation),
        "real_salary": _safe(lambda: _real_salary(db, ipc), empty_salary),
        "savings": _safe(
            lambda: _savings(db, tipo_bce),
            {"idle_liquidity": 0.0, "tipo_bce": tipo_bce, "potential_monthly": None},
        ),
        "euribor": {
            "value": euribor,
            "year_ago": euribor_year_ago,
            "history": _safe(
                lambda: [{"period": p, "value": v} for p, v in _macro_series("euribor_12m")[-24:]],
                [],
            ),
        },
        "fiscal_calendar": _safe(_fiscal_calendar, []),
        "relevant_news": _safe(lambda: _relevant_news(db), []),
    }
