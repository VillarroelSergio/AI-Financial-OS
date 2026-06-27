from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import SessionLocal, create_tables
from app.modules.accounts.routes import router as accounts_router
from app.modules.ai.routes import router as ai_router
from app.modules.categories.routes import router as categories_router
from app.modules.dashboard.routes import router as dashboard_router
from app.modules.goals.routes import router as goals_router
from app.modules.imports.routes import router as imports_router
from app.modules.insights.routes import router as insights_router
from app.modules.investments.routes import router as investments_router
from app.modules.market_intelligence.api.routes import router as market_intelligence_router
from app.modules.rag.routes import router as rag_router
from app.modules.settings.routes import router as settings_router
from app.modules.transactions.routes import router as transactions_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    create_tables()
    db = SessionLocal()
    try:
        from app.seeds.categories import seed_categories
        from app.seeds.settings import seed_settings
        seed_categories(db)
        seed_settings(db)
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


app.include_router(accounts_router, prefix="/api/accounts", tags=["accounts"])
app.include_router(categories_router, prefix="/api/categories", tags=["categories"])
app.include_router(transactions_router, prefix="/api/transactions", tags=["transactions"])
app.include_router(imports_router, prefix="/api/imports", tags=["imports"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(investments_router, prefix="/api/investments", tags=["investments"])
app.include_router(goals_router, prefix="/api/goals", tags=["goals"])
app.include_router(insights_router, prefix="/api/insights", tags=["insights"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
app.include_router(rag_router, prefix="/api/rag", tags=["rag"])
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])
app.include_router(market_intelligence_router, prefix="/api/market-intelligence", tags=["market_intelligence"])
