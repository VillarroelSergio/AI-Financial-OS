import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core import database as db_module
from app.core.database import create_tables
from app.modules.accounts.routes import router as accounts_router
from app.modules.ai.routes import router as ai_router
from app.modules.budgets.routes import router as budgets_router
from app.modules.cashflow.routes import router as cashflow_router
from app.modules.categories.routes import router as categories_router
from app.modules.dashboard.routes import router as dashboard_router
from app.modules.financial_knowledge.router import router as financial_knowledge_router
from app.modules.goals.routes import router as goals_router
from app.modules.household_bills.routes import router as household_bills_router
from app.modules.imports.routes import router as imports_router
from app.modules.insights.routes import router as insights_router
from app.modules.investments.portfolio_import_routes import router as portfolio_import_router
from app.modules.investments.price_coverage_routes import router as price_coverage_router
from app.modules.investments.reconciliation_routes import router as reconciliation_router
from app.modules.investments.routes import router as investments_router
from app.modules.market_intelligence.api.routes import router as market_intelligence_router
from app.modules.net_worth.routes import router as net_worth_router
from app.modules.rag.routes import router as rag_router
from app.modules.recurring.routes import router as recurring_router
from app.modules.security.routes import router as security_router
from app.modules.settings.routes import router as settings_router
from app.modules.transactions.routes import router as transactions_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    create_tables()
    from app.modules.insights import repository as insights_repo
    insights_repo._migrate_legacy_json()  # D3: dismissals JSON → SQLite (one-shot)
    db = db_module.SessionLocal()
    try:
        from app.seeds.categories import seed_categories
        from app.seeds.settings import seed_settings
        seed_categories(db)
        seed_settings(db)

        # Previews abandonados: batches 'validated' de hace más de 7 días y sus filas.
        from datetime import datetime, timedelta, timezone

        from app.models.import_batch import ImportBatch, ImportRow

        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        stale_ids = [
            b.id
            for b in db.query(ImportBatch).filter(
                ImportBatch.status == "validated", ImportBatch.created_at < cutoff
            )
        ]
        if stale_ids:
            db.query(ImportRow).filter(ImportRow.import_batch_id.in_(stale_ids)).delete()
            db.query(ImportBatch).filter(ImportBatch.id.in_(stale_ids)).delete()
            db.commit()
    finally:
        db.close()

    from app.modules.market_intelligence.ingestion.startup import launch_startup_ingest
    launch_startup_ingest()

    yield


app = FastAPI(title="AI Financial OS", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",
        "tauri://localhost",
        "http://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def require_api_token(request: Request, call_next):
    # Solo se exige si el launcher configuró token (producción empaquetada).
    # /health queda abierto: el launcher lo usa para saber cuándo está listo.
    # Se lee de os.environ en cada request para ser testeable y no cachear un
    # token que el launcher inyecta después del import.
    token = os.environ.get("FINOS_API_TOKEN")
    if token and request.url.path != "/health" and request.method != "OPTIONS":
        if request.headers.get("x-api-token") != token:
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "UNAUTHORIZED", "message": "Token de API inválido", "details": {}}},
            )
    return await call_next(request)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


app.include_router(accounts_router, prefix="/api/accounts", tags=["accounts"])
app.include_router(categories_router, prefix="/api/categories", tags=["categories"])
app.include_router(transactions_router, prefix="/api/transactions", tags=["transactions"])
app.include_router(imports_router, prefix="/api/imports", tags=["imports"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(investments_router, prefix="/api/investments", tags=["investments"])
app.include_router(price_coverage_router, prefix="/api/investments/price-coverage", tags=["investments"])
app.include_router(reconciliation_router, prefix="/api/investments", tags=["investments"])
app.include_router(portfolio_import_router, prefix="/api/investments/import", tags=["investments"])
app.include_router(goals_router, prefix="/api/goals", tags=["goals"])
app.include_router(insights_router, prefix="/api/insights", tags=["insights"])
app.include_router(net_worth_router, prefix="/api/net-worth", tags=["net_worth"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
app.include_router(rag_router, prefix="/api/rag", tags=["rag"])
app.include_router(security_router, prefix="/api/security", tags=["security"])
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])
app.include_router(market_intelligence_router, prefix="/api/market-intelligence", tags=["market_intelligence"])
app.include_router(financial_knowledge_router, prefix="/api/financial-knowledge", tags=["financial_knowledge"])
app.include_router(budgets_router, prefix="/api/budgets", tags=["budgets"])
app.include_router(recurring_router, prefix="/api/recurring", tags=["recurring"])
app.include_router(cashflow_router, prefix="/api/cashflow", tags=["cashflow"])
app.include_router(household_bills_router, prefix="/api/household-bills", tags=["household_bills"])
