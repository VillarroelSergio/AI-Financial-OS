import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from both the repository root and the market-data-poc directory.
# The POC-local file wins when both define the same key.
_pkg_dir = Path(__file__).parent.parent
load_dotenv(_pkg_dir.parent / ".env")
load_dotenv(_pkg_dir / ".env")


def get_api_key(provider_name: str) -> str | None:
    """Return the API key for the given provider, or None if not set."""
    env_var = f"{provider_name.upper().replace(' ', '_').replace('-', '_')}_API_KEY"
    return os.environ.get(env_var)


def get_timeout() -> int:
    """Return the HTTP timeout in seconds (default 10)."""
    return int(os.environ.get("POC_TIMEOUT", "10"))


def get_workers() -> int:
    """Return the number of concurrent worker threads (default 5)."""
    return int(os.environ.get("POC_WORKERS", "5"))
