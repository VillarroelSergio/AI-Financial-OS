"""Conciliación Monefy ↔ bancos.

Monefy es la fuente de verdad del gasto personal (importes reales, incluidos
gastos compartidos donde el banco muestra el total). Cada movimiento bancario
pendiente se empareja con su gasto Monefy: si el emparejamiento es de alta
confianza queda excluido de la analítica (su gemelo Monefy ya cuenta) y hereda
categoría en ambos sentidos.
"""

import unicodedata
from dataclasses import dataclass
from datetime import date as date_cls, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.transaction import Transaction

MATCH_WINDOW_DAYS = 3
AUTO_LINK_THRESHOLD = 0.75
SUGGESTION_THRESHOLD = 0.40

# Vocabulario Monefy (apuntes a mano) → comercios que aparecen en los bancos.
ALIASES: dict[str, set[str]] = {
    "tabaco": {"tabacos", "estanco"},
    "tobaco": {"tabacos", "estanco"},
    "merca": {"mercadona"},
    "compra": {"mercadona", "dia", "aldi", "lidl", "supercor"},
    "gpt": {"openai", "chatgpt", "claude"},
    "gym": {"fitness", "synergym"},
    "gimnasio": {"fitness", "synergym"},
    "gasolina": {"cepsa", "repsol", "plenergy", "avia", "gasolinera"},
    "luz": {"iberdrola", "endesa"},
    "agua": {"facsa", "tagus"},
    "tren": {"renfe", "alsa"},
    "ave": {"renfe"},
    "taxi": {"cabify", "bolt", "uber", "taxi"},
    "cine": {"cinesur", "cinema", "yelmo"},
    "veterinario": {"veterinaria", "guaw"},
    "michis": {"guaw", "veterinaria"},
    "fruta": {"fruteria"},
    "farmacia": {"farmacia"},
    "office": {"microsoft"},
    "play": {"playstation"},
    "play5": {"playstation"},
    "burguer": {"burger"},
    "bueguer": {"burger"},
}

STOPWORDS = {
    "de", "del", "la", "el", "los", "las", "con", "y", "a", "en", "por",
    "adeudo", "pago", "compra", "n", "sa", "sl", "s.l.", "toledo", "madrid",
}


def _normalize(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    tokens = [t.strip(".,*#:;()'-") for t in text.split()]
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]


def _description_score(monefy_desc: str, bank_desc: str) -> float:
    monefy_tokens, bank_tokens = _normalize(monefy_desc), _normalize(bank_desc)
    if not monefy_tokens or not bank_tokens:
        return 0.0
    bank_set = set(bank_tokens)
    hits = 0
    for token in monefy_tokens:
        aliases = ALIASES.get(token, set()) | {token}
        if any(a in b or b in a for a in aliases for b in bank_set if len(a) > 3 or a == b):
            hits += 1
    return hits / len(monefy_tokens)


def _amount_score(monefy_amount: Decimal, bank_amount: Decimal) -> float:
    m, b = abs(monefy_amount), abs(bank_amount)
    if not b:
        return 0.0
    diff = abs(m - b)
    if diff <= Decimal("0.6") or diff / b <= Decimal("0.02"):
        return 1.0
    # Gasto compartido: Monefy registra la parte personal (menor que el total).
    if Decimal("0.25") <= m / b < 1:
        return 0.5
    return 0.0


def _date_score(a: str, b: str) -> float:
    days = abs((date_cls.fromisoformat(a) - date_cls.fromisoformat(b)).days)
    return max(0.0, 1 - days / (MATCH_WINDOW_DAYS + 1))


@dataclass
class Match:
    bank_tx: Transaction
    monefy_tx: Transaction
    score: float


def _score(bank_tx: Transaction, monefy_tx: Transaction) -> float:
    amount = _amount_score(monefy_tx.amount, bank_tx.amount)
    desc = _description_score(monefy_tx.description or "", bank_tx.description or "")
    date = _date_score(monefy_tx.date, bank_tx.date)
    if amount == 0.0:
        return 0.0
    # Importe parcial (compartido) solo es creíble si la descripción encaja.
    if amount < 1.0 and desc < 0.5:
        return 0.0
    return 0.45 * amount + 0.35 * desc + 0.20 * date


def find_matches(db: Session) -> list[Match]:
    """Mejor candidato Monefy para cada movimiento bancario pendiente."""
    pending = (
        db.query(Transaction)
        .filter(
            Transaction.analytics_scope == "pending",
            Transaction.type.in_(["income", "expense"]),
        )
        .all()
    )
    if not pending:
        return []
    linked_ids = {
        row[0]
        for row in db.query(Transaction.linked_transaction_id)
        .filter(Transaction.linked_transaction_id.isnot(None))
        .all()
    }
    anchors_query = db.query(Transaction).filter(
        Transaction.analytics_scope == "personal",
        Transaction.source_name == "Monefy",
        Transaction.type.in_(["income", "expense"]),
    )
    if linked_ids:
        anchors_query = anchors_query.filter(~Transaction.id.in_(linked_ids))
    anchors = anchors_query.all()
    # Índice por fecha para no hacer producto cartesiano completo.
    by_date: dict[str, list[Transaction]] = {}
    for anchor in anchors:
        by_date.setdefault(anchor.date, []).append(anchor)

    matches: list[Match] = []
    used_anchor_ids: set[str] = set()
    # Bancarios más antiguos primero: el emparejado es greedy y estable.
    for bank_tx in sorted(pending, key=lambda t: t.date):
        bank_date = date_cls.fromisoformat(bank_tx.date)
        best: Match | None = None
        for offset in range(-MATCH_WINDOW_DAYS, MATCH_WINDOW_DAYS + 1):
            day = (bank_date + timedelta(days=offset)).isoformat()
            for anchor in by_date.get(day, []):
                if anchor.id in used_anchor_ids or anchor.type != bank_tx.type:
                    continue
                score = _score(bank_tx, anchor)
                if score >= SUGGESTION_THRESHOLD and (best is None or score > best.score):
                    best = Match(bank_tx, anchor, score)
        if best:
            used_anchor_ids.add(best.monefy_tx.id)
            matches.append(best)
    return matches


def reconcile(db: Session) -> dict:
    """Enlaza automáticamente los emparejamientos de alta confianza y
    propaga categorías; devuelve estadísticas. No hace commit."""
    matches = find_matches(db)
    linked = 0
    merchant_categories: dict[str, str] = {}
    for match in matches:
        if match.score < AUTO_LINK_THRESHOLD:
            continue
        bank_tx, monefy_tx = match.bank_tx, match.monefy_tx
        bank_tx.linked_transaction_id = monefy_tx.id
        bank_tx.analytics_scope = "excluded"
        if monefy_tx.category_id and not bank_tx.category_id:
            bank_tx.category_id = monefy_tx.category_id
        if bank_tx.category_id:
            merchant = " ".join(_normalize(bank_tx.description or ""))
            if merchant:
                merchant_categories.setdefault(merchant, bank_tx.category_id)
        linked += 1
    # Comercios recurrentes: la categoría aprendida se aplica al resto de
    # movimientos del mismo comercio que siguen sin categoría.
    categorized = 0
    if merchant_categories:
        uncategorized = (
            db.query(Transaction)
            .filter(Transaction.category_id.is_(None), Transaction.source == "csv")
            .all()
        )
        for tx in uncategorized:
            merchant = " ".join(_normalize(tx.description or ""))
            if merchant in merchant_categories:
                tx.category_id = merchant_categories[merchant]
                categorized += 1
    return {
        "auto_linked": linked,
        "categories_propagated": categorized,
        "suggestions": len(matches) - linked,
    }
