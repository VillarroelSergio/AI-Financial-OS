# Scoring

Provider score combines:

- Data quality
- Reliability
- Coverage breadth
- Geographic coverage
- Historical depth
- Update frequency
- Latency
- Integration complexity
- Legal risk

Recommendations:

- `principal`: score >= 75
- `secundario`: score >= 50
- `fallback`: score >= 30
- `descartado`: score < 30

The POC now also exposes `ProviderScore` for future richer telemetry around availability, latency, coverage, history, quality, frequency and reliability.
