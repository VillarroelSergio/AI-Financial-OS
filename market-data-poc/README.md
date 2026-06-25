# Market Data POC

Standalone proof of concept for testing free financial and macroeconomic data providers.

The package is intentionally isolated from the main application: it does not import backend code, does not write to the database, and runs as a CLI-only explorer.

## Setup

```powershell
cd AI-Financial-OS\market-data-poc
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

Optional API keys can be placed in `.env`:

```env
ALPHA_VANTAGE_API_KEY=...
FINNHUB_API_KEY=...
FMP_API_KEY=...
TWELVE_DATA_API_KEY=...
```

Providers without a required key run with no extra configuration.

## Usage

```powershell
python run_poc.py --providers all --output json,csv,report --timeout 10 --workers 5
```

Provider filters:

- `all`
- `spain`
- `europe`
- `usa`
- `global`

Output formats can be combined with commas: `json,csv,report`.

Generated artifacts are written under `output/`:

- `output/json/`: one JSON file per provider result
- `output/csv/`: flattened records
- `output/reports/`: Markdown evaluation report

## Scope

In-scope providers include Spanish public sources, European macro APIs, US public data APIs, global market data sources, RSS feeds, and optional freemium APIs.

Scrapy spiders are included only as fallback prototypes and are not part of the main runner.
