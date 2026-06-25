# Provider Orchestrator

The orchestrator is the access boundary for future application code.

Do not call providers directly from application workflows. Select a capability and let the orchestrator resolve:

```text
primary -> secondary -> fallback -> scraper
```

Implemented pieces:

- `ProviderSelector`: chooses providers by declared capability and priority.
- `ProviderOrchestrator.fetch()`: executes failover transparently.
- `ProviderOrchestrator.health()`: reports online, degraded or offline status.
- `LocalTTLCache`: avoids repeated downloads with configurable TTL.
- `compare_equivalent_values()`: detects spreads when providers return the same symbol or macro series.

Current CLI commands:

```bash
python run_poc.py market:poc
python run_poc.py market:health
python run_poc.py market:coverage
python run_poc.py market:providers
python run_poc.py market:compare
python run_poc.py market:report
python run_poc.py market:cache:clear
python run_poc.py market:test
```
