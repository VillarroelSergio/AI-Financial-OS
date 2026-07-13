"""Deterministic post-processing of LLM replies.

Small local models ignore formatting instructions from the system prompt, so we
clean their output deterministically before it reaches the UI. This only does
*safe* transforms (never rewrites meaning): strips emojis, drops horizontal-rule
separators the models love to emit, and normalises whitespace.

AI-4 adds `enforce_advice_guardrail`: we do NOT rewrite the body (a blind regex
replace corrupts legitimate text like "garantizado por el FGD"). Instead, when a
*high-precision* buy/sell directive or guaranteed-return claim is detected, we
append a single neutral disclaimer footer — detection + reframing, no corruption.
"""
from __future__ import annotations

import re

# Emoji + pictographic ranges (BMP + astral). Deliberately broad; financial copy
# has no legitimate use for them.
_EMOJI = re.compile(
    "["
    "\U0001F300-\U0001FAFF"  # symbols, pictographs, emoji
    "\U00002600-\U000027BF"  # misc symbols + dingbats
    "\U0001F1E6-\U0001F1FF"  # regional indicators (flags)
    "\U00002190-\U000021FF"  # arrows
    "\U0000FE00-\U0000FE0F"  # variation selectors
    "\U00002B00-\U00002BFF"  # misc symbols and arrows
    "]",
    flags=re.UNICODE,
)

# Markdown horizontal rules: *** / --- / ___ (3+), on their own line.
_HR = re.compile(r"^\s*([*_-])\1{2,}\s*$", flags=re.MULTILINE)

# 3+ consecutive newlines -> just a paragraph break.
_MULTI_NL = re.compile(r"\n{3,}")

# AI-4: directivas de inversión de alta precisión. Deliberadamente estrechas para
# no marcar usos legítimos ("poder de compra", "garantizado por el FGD"):
#   - segunda persona aconsejando comprar/vender/invertir;
#   - rentabilidad/retorno/ganancia/beneficio calificados de "garantizad*".
_ADVICE = re.compile(
    r"\b(deberías|deberias|debes|te\s+(?:recomiendo|aconsejo|sugiero))\s+"
    r"(comprar|vender|invertir|aportar|retirar|traspasar)\b"
    r"|\b(rentabilidad|retorno|ganancias?|beneficios?)\s+\w*\s*garantizad"
    r"|\bgarantizad\w*\s+(rentabilidad|retorno|ganancias?|beneficios?)\b",
    flags=re.IGNORECASE,
)

_DISCLAIMER = (
    "Nota: esto es información sobre tus datos, no una recomendación de compra o "
    "venta; ninguna rentabilidad futura está garantizada."
)


def enforce_advice_guardrail(text: str | None) -> str | None:
    """Si el texto contiene una directiva de compra/venta o promete rentabilidad
    garantizada, añade UNA nota neutral al final. No reescribe el cuerpo (evita
    corromper texto legítimo). None/empty pasa sin cambios."""
    if not text or _DISCLAIMER in text:
        return text
    if _ADVICE.search(text):
        return f"{text}\n\n{_DISCLAIMER}"
    return text


def sanitize_response(text: str | None) -> str | None:
    """Clean an LLM reply. None/empty passes through unchanged."""
    if not text:
        return text
    text = _EMOJI.sub("", text)
    text = _HR.sub("", text)
    text = _MULTI_NL.sub("\n\n", text)
    # Trim trailing spaces per line and surrounding blank lines.
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text.strip()


if __name__ == "__main__":
    # Self-check: run `python -m app.modules.ai.prompts.guardrails`
    assert sanitize_response(None) is None
    assert sanitize_response("") == ""
    assert sanitize_response("Hola 👋 mundo 🚀") == "Hola  mundo"
    assert sanitize_response("uno\n***\ndos") == "uno\n\ndos"
    assert sanitize_response("uno\n---\ndos") == "uno\n\ndos"
    assert sanitize_response("a\n\n\n\n\nb") == "a\n\nb"
    assert sanitize_response("trailing   \nspace") == "trailing\nspace"
    # Does NOT touch legitimate financial words or markdown emphasis/lists.
    kept = "El **fondo** está garantizado por el FGD.\n- punto uno\n1. paso"
    assert sanitize_response(kept) == kept, sanitize_response(kept)
    # enforce_advice_guardrail: añade nota SOLO ante directivas de alta precisión.
    assert enforce_advice_guardrail(None) is None
    assert enforce_advice_guardrail("Tu gasto subió un 4%.") == "Tu gasto subió un 4%."
    # No falsos positivos en usos legítimos:
    assert enforce_advice_guardrail("El fondo está garantizado por el FGD.") == "El fondo está garantizado por el FGD."
    assert enforce_advice_guardrail("Tu poder de compra bajó.") == "Tu poder de compra bajó."
    # Sí marca directivas reales:
    assert _DISCLAIMER in enforce_advice_guardrail("Creo que deberías comprar acciones de X.")
    assert _DISCLAIMER in enforce_advice_guardrail("Te recomiendo vender ese fondo.")
    assert _DISCLAIMER in enforce_advice_guardrail("Ofrece una rentabilidad garantizada del 8%.")
    # Idempotente: no duplica la nota.
    once = enforce_advice_guardrail("Deberías invertir en bonos.")
    assert enforce_advice_guardrail(once) == once
    print("guardrails self-check ok")
