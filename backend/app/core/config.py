from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./data/financial.db"
    DUCKDB_PATH: str = "./data/analytics.duckdb"  # financial_knowledge (fuera de ECO-3b)
    MI_SQLITE_PATH: str = "./data/market_intelligence.db"  # ECO-3b: MI migrado a SQLite WAL

    # ── AI Assistant ──────────────────────────────────────────────────────────
    AI_ASSISTANT_ENABLED: bool = True
    AI_DEFAULT_PROVIDER: str = "ollama"
    AI_DEFAULT_MODEL: str = "qwen3-coder:30b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LMSTUDIO_BASE_URL: str = "http://localhost:1234/v1"
    AI_REMOTE_PROVIDERS_ENABLED: bool = False
    AI_MAX_CONTEXT_TOKENS: int = 32768
    AI_MAX_OUTPUT_TOKENS: int = 4096
    AI_ENABLE_STREAMING: bool = True
    AI_ENABLE_TOOL_TRACE: bool = True

    # ── Market data providers (opcionales, todos gratuitos) ───────────────────
    # Dejar vacíos si no se dispone de key — los proveedores se desactivarán.
    ALPHA_VANTAGE_API_KEY: str = ""
    FINNHUB_API_KEY: str = ""
    FMP_API_KEY: str = ""
    TWELVEDATA_API_KEY: str = ""
    POLYGON_API_KEY: str = ""
    EIA_API_KEY: str = ""
    AEMET_API_KEY: str = ""
    OPENFIGI_API_KEY: str = ""

    # ── Economic data providers ───────────────────────────────────────────────
    FRED_API_KEY: str = ""


settings = Settings()
