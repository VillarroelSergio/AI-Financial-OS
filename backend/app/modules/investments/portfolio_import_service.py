"""Portfolio Import Assistant — backend service.

Conceptual data-origin model:
  captured   – value extracted from screenshot/pasted text
  estimated  – calculated (e.g. cost from value + return%)
  confirmed  – manually verified or entered by the user
  provider   – fetched from a market data provider
  manual     – user-entered, no auto-update

Import-position statuses:
  READY               – instrument resolved + price available
  REQUIRES_CONFIRMATION – ambiguous ticker; user must confirm
  NO_PRICE            – instrument found but no current price
  MANUAL              – user marked as manual (no auto-update)
  REVIEW              – some data missing or uncertain
  ERROR               – technical failure during validation

Security constraints honoured here:
  – No image bytes are forwarded to any external service.
  – No financial data is written to logs.
  – Holdings are only created after explicit user confirmation.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional

from sqlalchemy.orm import Session

from app.models.investment import Holding, InvestmentAsset
from app.modules.investments.asset_resolution import resolve_asset
from app.modules.investments.price_coverage_audit import audit_asset

# ── Number / currency helpers ─────────────────────────────────────────────────

_CURRENCY_SYMBOLS: dict[str, str] = {
    "€": "EUR",
    "$": "USD",
    "£": "GBP",
    "A$": "AUD",
    "¥": "JPY",
    "CHF": "CHF",
}

_CURRENCY_CODES = {"EUR", "USD", "GBP", "AUD", "CHF", "JPY"}


def _is_spanish_thousands_number(value: str) -> bool:
    """Return whether value uses the Spanish thousands format (1.234,56)."""
    integer, separator, decimal = value.partition(",")
    groups = integer.split(".")
    return (
        bool(separator)
        and decimal.isdecimal()
        and len(groups) > 1
        and 1 <= len(groups[0]) <= 3
        and groups[0].isdecimal()
        and all(len(group) == 3 and group.isdecimal() for group in groups[1:])
    )


def _parse_number(s: str) -> Optional[float]:
    """Parse a number string that may use comma or dot as decimal separator."""
    s = s.strip().replace(" ", "").replace("\xa0", "")
    if not s:
        return None
    # Spanish thousands format: 1.234,56
    if _is_spanish_thousands_number(s):
        return float(s.replace(".", "").replace(",", "."))
    if "," in s and "." not in s:
        return float(s.replace(",", "."))
    if "," in s and "." in s:
        if s.rindex(",") > s.rindex("."):
            return float(s.replace(".", "").replace(",", "."))
        return float(s.replace(",", ""))
    try:
        return float(s)
    except ValueError:
        return None


def _strip_currency(s: str) -> tuple[Optional[str], str]:
    """Return (currency_code, cleaned_string) by removing currency symbols."""
    s = s.strip()
    # Try multi-char prefixes first
    for sym, code in sorted(_CURRENCY_SYMBOLS.items(), key=lambda x: -len(x[0])):
        if sym in s:
            return code, s.replace(sym, "").strip()
    # Try trailing currency codes (e.g. "140.15 EUR")
    for code in _CURRENCY_CODES:
        if s.upper().endswith(code):
            return code, s[: -len(code)].strip()
    return None, s


# ── Raw position (output of text parser) ─────────────────────────────────────

@dataclass
class RawPosition:
    raw_name: str
    quantity: Optional[float]
    current_value: Optional[float]
    current_value_currency: Optional[str]
    return_pct: Optional[float]
    raw_text: str


def _parse_block(lines: list[str]) -> Optional[RawPosition]:
    """Convert a list of consecutive text lines into a RawPosition."""
    if not lines:
        return None

    name = lines[0].strip()
    if not name or re.match(r"^[\d.,+\-%€$£]+$", name):
        return None

    raw_text = "\n".join(lines)
    quantity: Optional[float] = None
    current_value: Optional[float] = None
    current_value_currency: Optional[str] = None
    return_pct: Optional[float] = None

    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue

        # Return percentage line: optional sign, digits, separator, digits, %
        pct_m = re.fullmatch(r"([+-]?\s*\d+[.,]\d+)\s*%", line)
        if pct_m and return_pct is None:
            return_pct = _parse_number(pct_m.group(1).replace(" ", ""))
            continue

        # Value with currency symbol
        currency, cleaned = _strip_currency(line)
        if currency:
            v = _parse_number(cleaned)
            if v is not None and current_value is None:
                current_value = v
                current_value_currency = currency
            continue

        # Quantity line — may be prefixed with "x" or "×"
        qty_line = re.sub(r"^[xX×]\s*", "", line)
        q = _parse_number(qty_line)
        if q is not None and quantity is None:
            quantity = q

    return RawPosition(
        raw_name=name,
        quantity=quantity,
        current_value=current_value,
        current_value_currency=current_value_currency,
        return_pct=return_pct,
        raw_text=raw_text,
    )


def parse_text_positions(text: str) -> list[RawPosition]:
    """Parse pasted portfolio text (multi-line blocks) into RawPositions.

    Expected broker format (one position per blank-line-separated block):
        Apple
        x 0,564555
        140,15 €
        +38,76 %

    Also tolerates single-line formats mixed in.
    """
    blocks: list[list[str]] = []
    current: list[str] = []

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped:
            current.append(stripped)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)

    positions: list[RawPosition] = []
    for block in blocks:
        pos = _parse_block(block)
        if pos:
            positions.append(pos)

    return positions


# ── Image extraction via local vision model ──────────────────────────────────

_VISION_PROMPT = (
    "Extrae las posiciones de inversión visibles en esta captura de pantalla de un broker. "
    "Devuelve SOLO un array JSON válido, sin markdown ni texto adicional, con un objeto por posición: "
    '[{"name": "<nombre del activo>", "quantity": <número o null>, '
    '"current_value": <valor actual numérico o null>, "currency": "<EUR|USD|GBP o null>", '
    '"return_pct": <rentabilidad % numérica con signo o null>}]. '
    "Usa punto como separador decimal. Si un dato no es visible, usa null. "
    "Si no hay posiciones, devuelve []."
)


async def extract_positions_from_image(
    image_b64: str, media_type: str, provider_name: str | None = None
) -> list[RawPosition]:
    """Extrae posiciones de una captura usando el modelo de visión IA local.

    Lanza RuntimeError con mensaje legible si el proveedor no está disponible
    o la respuesta no es JSON interpretable (p. ej. modelo sin visión).
    """
    from app.modules.ai.service import get_provider

    provider = get_provider(provider_name)
    health = await provider.health()
    if not health.available:
        raise RuntimeError(
            f"El proveedor IA local ({provider.name}) no está disponible: {health.error or 'offline'}. "
            "Arranca Ollama o LM Studio con un modelo de visión (p. ej. qwen2.5-vl, llava)."
        )

    if provider.name == "ollama":
        message = {"role": "user", "content": _VISION_PROMPT, "images": [image_b64]}
    else:
        # OpenAI-compatible (LM Studio): content como array texto + imagen
        message = {
            "role": "user",
            "content": [
                {"type": "text", "text": _VISION_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_b64}"}},
            ],
        }

    response = await provider.chat(messages=[message], tools=None)
    text = (response.content or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        raise RuntimeError(
            "El modelo no devolvió posiciones en formato JSON. "
            "Comprueba que el modelo cargado soporta visión (qwen2.5-vl, llava, minicpm-v)."
        )

    import json as _json

    try:
        items = _json.loads(text[start : end + 1])
    except _json.JSONDecodeError as exc:
        raise RuntimeError(f"Respuesta del modelo no interpretable como JSON: {exc}") from exc

    positions: list[RawPosition] = []
    for item in items:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        currency = (item.get("currency") or "").upper() or None

        def _num(value: object) -> Optional[float]:
            try:
                return float(value) if value is not None else None
            except (TypeError, ValueError):
                return None

        positions.append(
            RawPosition(
                raw_name=str(item["name"]).strip(),
                quantity=_num(item.get("quantity")),
                current_value=_num(item.get("current_value")),
                current_value_currency=currency,
                return_pct=_num(item.get("return_pct")),
                raw_text=_json.dumps(item, ensure_ascii=False),
            )
        )
    return positions


# ── Validated position (output after instrument resolution + price coverage) ──

@dataclass
class ValidatedPosition:
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Captured data (from pasted text or manual entry)
    raw_name: str = ""
    quantity: Optional[float] = None
    current_value: Optional[float] = None
    current_value_currency: Optional[str] = None
    return_pct: Optional[float] = None
    raw_text: str = ""

    # Estimated data
    estimated_cost: Optional[float] = None
    is_cost_estimated: bool = False

    # Instrument resolution
    selected_ticker: Optional[str] = None
    exchange: Optional[str] = None
    currency: Optional[str] = None
    asset_type: str = "stock"
    resolution_status: str = "unavailable"  # resolved|ambiguous|unavailable
    resolution_confidence: float = 0.0
    requires_confirmation: bool = False

    # Price coverage
    price: Optional[float] = None
    price_currency: Optional[str] = None
    eur_price: Optional[float] = None
    fx_rate: Optional[float] = None
    coverage_status: Optional[str] = None

    # Import status
    import_status: str = "REVIEW"
    notes: list[str] = field(default_factory=list)


# ── Cost estimation ───────────────────────────────────────────────────────────

def estimate_cost(current_value: float, return_pct: float) -> float:
    """Estimated cost basis from current value and percentage return.

    Formula: cost ≈ current_value / (1 + return_pct / 100)

    Marked as estimated — never used for fiscal or exact accounting.
    """
    divisor = 1.0 + return_pct / 100.0
    if abs(divisor) < 1e-9:
        return current_value
    return round(current_value / divisor, 2)


# ── Import-status classifier ──────────────────────────────────────────────────

def _classify_import_status(
    resolution_status: str,
    requires_confirmation: bool,
    coverage_status: Optional[str],
) -> tuple[str, list[str]]:
    notes: list[str] = []

    if resolution_status == "unavailable":
        notes.append("No se encontró instrumento para este activo. Puede añadirlo manualmente.")
        return "REVIEW", notes

    if resolution_status == "ambiguous" or requires_confirmation:
        notes.append("El ticker encontrado requiere confirmación antes de importar.")
        return "REQUIRES_CONFIRMATION", notes

    # Instrument resolved
    if coverage_status in ("OK", "FX_PENDING"):
        return "READY", notes

    if coverage_status == "UNAVAILABLE":
        notes.append("No hay precio disponible en los proveedores actuales. Puede importar como manual.")
        return "NO_PRICE", notes

    notes.append("Revisa los datos antes de importar.")
    return "REVIEW", notes


# ── Main validation function ──────────────────────────────────────────────────

def validate_position(
    raw_name: str,
    quantity: Optional[float] = None,
    current_value: Optional[float] = None,
    current_value_currency: Optional[str] = None,
    return_pct: Optional[float] = None,
    raw_text: str = "",
) -> ValidatedPosition:
    """Resolve instrument and fetch price coverage for a single position.

    Does not access the database — purely calls existing resolution and audit
    services. Safe to call in bulk.
    """
    pos = ValidatedPosition(
        raw_name=raw_name,
        quantity=quantity,
        current_value=current_value,
        current_value_currency=current_value_currency,
        return_pct=return_pct,
        raw_text=raw_text,
    )

    # Estimated cost
    if current_value is not None and return_pct is not None:
        pos.estimated_cost = estimate_cost(current_value, return_pct)
        pos.is_cost_estimated = True

    # Instrument resolution
    resolution = resolve_asset(raw_name)
    pos.resolution_status = resolution.status
    pos.requires_confirmation = False

    if resolution.status == "resolved" and resolution.selected:
        sel = resolution.selected
        pos.selected_ticker = sel.ticker
        pos.exchange = sel.exchange
        pos.currency = sel.currency
        pos.asset_type = sel.asset_type
        pos.resolution_confidence = sel.confidence
        pos.requires_confirmation = sel.requires_confirmation

    elif resolution.status == "ambiguous" and resolution.candidates:
        cand = resolution.candidates[0]
        pos.selected_ticker = cand.ticker
        pos.exchange = cand.exchange
        pos.currency = cand.currency
        pos.asset_type = cand.asset_type
        pos.resolution_confidence = cand.confidence
        pos.requires_confirmation = True

    # Price coverage (only for resolved assets; skip for ambiguous/unavailable
    # to avoid noisy provider calls)
    if resolution.status == "resolved" and not pos.requires_confirmation:
        audit = audit_asset(raw_name)
        pos.price = audit.price
        pos.price_currency = audit.price_currency
        pos.eur_price = audit.eur_price
        pos.fx_rate = audit.fx_rate
        pos.coverage_status = audit.status

    elif pos.requires_confirmation or resolution.status == "ambiguous":
        pos.coverage_status = "AMBIGUOUS"

    else:
        pos.coverage_status = "UNAVAILABLE"

    # Import status
    import_status, notes = _classify_import_status(
        pos.resolution_status,
        pos.requires_confirmation,
        pos.coverage_status,
    )
    pos.import_status = import_status
    pos.notes = notes

    return pos


# ── Duplicate detection ───────────────────────────────────────────────────────

_TICKER_ALIASES: dict[str, str] = {
    "BRK.B": "BRK-B",
    "BRK/B": "BRK-B",
    "BRK_B": "BRK-B",
}


def _normalize_ticker(ticker: str) -> str:
    t = ticker.upper().strip()
    return _TICKER_ALIASES.get(t, t)


def find_duplicates(ticker: str, account_id: Optional[str], db: Session) -> list[str]:
    """Return holding IDs in the same account that match ticker (normalized)."""
    needle = _normalize_ticker(ticker)
    q = db.query(Holding)
    if account_id:
        q = q.filter(Holding.account_id == account_id)
    holdings = q.all()

    matches: list[str] = []
    for h in holdings:
        asset = db.query(InvestmentAsset).filter(InvestmentAsset.id == h.asset_id).first()
        if asset and asset.ticker and _normalize_ticker(asset.ticker) == needle:
            matches.append(h.id)
    return matches


# ── Holding creation ──────────────────────────────────────────────────────────

@dataclass
class ConfirmedPosition:
    raw_name: str
    ticker: Optional[str]
    exchange: Optional[str]
    currency: str
    asset_type: str
    quantity: float
    average_price: float         # confirmed average purchase price (or estimated cost/qty)
    current_price: Optional[float]
    current_price_currency: str
    price_source: str            # "auto" | "manual"
    account_id: str
    is_manual: bool = False
    notes: list[str] = field(default_factory=list)
    is_cost_estimated: bool = False


def create_holding_from_import(
    confirmed: ConfirmedPosition,
    db: Session,
) -> Holding:
    """Create an InvestmentAsset + Holding from a confirmed import position.

    Called only after explicit user confirmation — never automatically.
    """
    # Create or reuse asset
    existing_asset = None
    if confirmed.ticker:
        existing_asset = (
            db.query(InvestmentAsset)
            .filter(InvestmentAsset.ticker == confirmed.ticker)
            .first()
        )

    if existing_asset is None:
        price_source = "manual" if confirmed.is_manual else confirmed.price_source
        asset = InvestmentAsset(
            name=confirmed.raw_name,
            ticker=confirmed.ticker,
            asset_type=confirmed.asset_type,
            currency=confirmed.currency,
            price_source=price_source,
        )
        db.add(asset)
        db.flush()
        asset_id = asset.id
    else:
        asset_id = existing_asset.id

    try:
        qty = Decimal(str(confirmed.quantity))
        avg = Decimal(str(confirmed.average_price))
    except InvalidOperation:
        qty = Decimal("0")
        avg = Decimal("0")

    current_price_dec: Optional[Decimal] = None
    if confirmed.current_price is not None:
        try:
            current_price_dec = Decimal(str(confirmed.current_price))
        except InvalidOperation:
            pass

    market_value = None
    if current_price_dec is not None:
        market_value = (qty * current_price_dec).quantize(Decimal("0.01"))

    holding = Holding(
        account_id=confirmed.account_id,
        asset_id=asset_id,
        quantity=qty,
        average_price=avg,
        current_price=current_price_dec,
        current_price_currency=confirmed.current_price_currency,
        current_price_updated_at=datetime.now(timezone.utc) if current_price_dec else None,
        market_value=market_value,
    )
    db.add(holding)
    db.commit()
    db.refresh(holding)
    return holding
