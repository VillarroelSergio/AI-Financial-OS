"""AI-3: el brief nunca bloquea (fallback determinista si el LLM cae) y es
idempotente por (scope, period)."""
import asyncio

from app.core import config
from app.modules.ai import analysis


async def _no_llm(_bundle, _provider, _model):
    """Simula el provider caído: render_narrative devuelve None → fallback."""
    return None, None, None


def test_generate_brief_falls_back_and_is_idempotent(client, monkeypatch):
    from app.core.database import SessionLocal

    monkeypatch.setattr(config.settings, "AI_ASSISTANT_ENABLED", True)
    monkeypatch.setattr(analysis, "render_narrative", _no_llm)

    db = SessionLocal()
    try:
        first = asyncio.run(analysis.generate_brief(db, "monthly_review", "2026-07"))
        # LLM caído → narrativa determinista no vacía, sin provider/model.
        assert first["narrative"]
        assert first["provider"] is None and first["model"] is None
        assert first["bundle"]["scope"] == "monthly_review"
        assert first["data_state"] == first["bundle"]["data_state"]

        # Regenerar el mismo (scope, period) no duplica: DELETE+INSERT.
        asyncio.run(analysis.generate_brief(db, "monthly_review", "2026-07"))
        briefs = analysis.list_briefs(db)
        same_period = [b for b in briefs if b["scope"] == "monthly_review" and b["period"] == "2026-07"]
        assert len(same_period) == 1

        assert analysis.get_brief(db, "monthly_review", "2026-07") is not None
    finally:
        db.close()


def test_build_bundle_rejects_unknown_scope(client):
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        for bad in (("bogus", "2026-07"), ("monthly_review", "2026/07")):
            try:
                analysis.build_bundle(db, *bad)
                assert False, f"expected ValueError for {bad}"
            except ValueError:
                pass
    finally:
        db.close()
