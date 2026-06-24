from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./data/financial.db"
    DUCKDB_PATH: str = "./data/analytics.duckdb"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LM_STUDIO_BASE_URL: str = "http://localhost:1234/v1"
    DEFAULT_AI_MODEL: str = "qwen"

    # ── Market data providers (opcionales, todos gratuitos) ───────────────────
    # Dejar vacíos si no se dispone de key — los proveedores se desactivarán.
    ALPHA_VANTAGE_API_KEY: str = ""
    FINNHUB_API_KEY: str = ""
    FMP_API_KEY: str = ""
    TWELVEDATA_API_KEY: str = ""


settings = Settings()
