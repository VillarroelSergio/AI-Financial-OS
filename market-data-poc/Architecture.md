# Market Data POC Architecture

The POC remains isolated from the main database, dashboard and AI modules.

```text
Application / CLI
  -> Provider Orchestrator
  -> Provider Selector
  -> Primary Provider
  -> Secondary Provider
  -> Fallback Provider
  -> Scraper
```

Core modules:

- `adapters/`: provider-specific access.
- `models/`: normalized records and provider evaluation models.
- `services/orchestrator.py`: capability-based selection and failover.
- `services/cache.py`: local TTL cache.
- `services/comparator.py`: cross-provider value comparison.
- `services/scorer.py`: provider ranking.
- `exporters/`: JSON, CSV and Markdown reports.

The next production phase should persist normalized records and provider telemetry, but this POC intentionally only writes local output files.
