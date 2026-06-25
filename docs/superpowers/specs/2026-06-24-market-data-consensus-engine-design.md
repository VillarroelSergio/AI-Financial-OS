# Market Data Consensus Engine — Design Spec
**Date:** 2026-06-24  
**Branch:** feat/multi-provider-market-data  
**Status:** Approved for implementation

---

## 1. Objective

Replace the current sequential fallback routing with a parallel fetch + consensus model that:

- Selects a **primary provider per asset_type** (not a global primary)
- Consults **validator providers in parallel**
- Resolves discrepancies via **median consensus** (when ≥3 valid prices)
- Scores data quality with a **weighted confidence system**
- Uses **Yahoo Finance only as last resort** (never primary, never validator)
- Adds **TwelveData** as a first-class provider
- Introduces a **RequestBudget** system to protect rate-limited free-tier APIs
- Produces **structured decision logs** for every quote resolution

No changes to `MarketQuoteInternal`, `/api/markets/quotes`, or existing tests.

---

## 2. New Files

| File | Purpose |
|---|---|
| `backend/app/modules/market_data/providers/twelvedata.py` | TwelveDataProvider implementation |
| `backend/app/modules/market_data/consensus.py` | ConsensusEngine — isolated, fully testable |
| `backend/app/modules/market_data/budget.py` | RequestBudget — daily per-provider request counter |

---

## 3. Provider Roles and Routing

### 3.1 Primary provider per asset_type

| asset_type | Primary | Validators | Budget-aware | Last resort |
|---|---|---|---|---|
| `index` | Stooq | TwelveData, Finnhub | AV (if budget) | Yahoo |
| `stocks_us` | Finnhub | TwelveData, FMP | AV (if budget) | Yahoo |
| `stocks_europe` | Stooq | TwelveData, FMP | — | Yahoo |
| `forex` | TwelveData | Finnhub, AV | AV (if budget) | Yahoo |
| `crypto` | Finnhub | TwelveData, AV | AV (if budget) | Yahoo |
| `commodity` | TwelveData | — | — | Yahoo |
| `bond` | Stooq | — | — | Yahoo |
| `volatility` | Stooq | — | — | Yahoo |
| `fundamentals` | FMP | Finnhub, AV | AV (if budget) | — |

### 3.2 Yahoo policy

```yaml
yahoo:
  enabled: true
  role: last_resort          # never primary, never validator
  diagnostic_mode: false     # true → include Yahoo in decision logs only (not in consensus)
```

Yahoo is consulted **only if valid_provider_count == 0** after the parallel fetch of all other providers. When used, the result carries `warning: yahoo_last_resort` and `confidence_score` is capped at 0.5.

### 3.3 TwelveData

- Free tier: 800 req/day, 8 req/min
- Symbol mappings added to `market_data_config.yaml` under each asset's `providers:` block
- Rate limit enforced by `RequestBudget` (conservative limit: 700/day to leave margin)

---

## 4. ConsensusEngine (`consensus.py`)

### 4.1 Interface

```python
@dataclass
class ConsensusResult:
    price: Optional[float]
    confidence_score: float
    selected_source: str          # provider name or "consensus_median"
    consensus_method: str         # "primary", "median", "single", "error"
    consensus_price: Optional[float]
    provider_count: int           # total providers attempted
    valid_provider_count: int     # providers that returned a valid price
    outliers: list[str]           # provider names discarded as outliers
    discarded_providers: list[str]
    warnings: list[str]           # normalized warning codes
    reason: str                   # human-readable decision explanation
    freshness_status: str
    source_type: str

class ConsensusEngine:
    def resolve(
        self,
        quotes: list[MarketQuoteInternal],
        asset_type: str,
        primary_provider: str,
    ) -> ConsensusResult:
        ...
```

### 4.2 Decision algorithm

```
1. Filter: price != None AND freshness_status != "error"
   → valid_quotes

2. IF len(valid_quotes) == 0:
   → consensus_method = "error"
   → return error result

3. IF len(valid_quotes) == 1:
   → consensus_method = "single"
   → price = valid_quotes[0].price
   → confidence_score = min(base_confidence * 0.6, 0.6)
   → warnings = ["unverified_single_provider"]
   → reason = "Only one provider returned valid data; result unverified"

4. IF len(valid_quotes) >= 2:
   a. Compute median of prices (use all valid prices)
   b. IF len(valid_quotes) >= 3:
        outlier_threshold = config.outlier_thresholds[asset_type]
        outliers = [q for q in valid_quotes
                    if abs(q.price - median) / median > outlier_threshold]
        valid_quotes = [q for q in valid_quotes if q not in outliers]
        recompute median from remaining valid_quotes
   c. Find primary quote (provider == primary_provider)
      IF primary_quote exists AND price within 1% of median:
        consensus_method = "primary"
        selected_source = primary_provider
        price = primary_quote.price
      ELSE:
        consensus_method = "median"
        selected_source = "consensus_median"
        price = median
        warnings += ["provider_mismatch"]
   d. weighted_confidence = compute_weighted_confidence(valid_quotes, asset_type)
   e. IF outliers: warnings += ["outlier_detected"]

5. Return ConsensusResult
```

### 4.3 Weighted confidence formula

```python
def compute_weighted_confidence(
    quotes: list[MarketQuoteInternal],
    asset_type: str,
) -> float:
    total_weight = 0.0
    weighted_sum = 0.0
    for q in quotes:
        base = config.provider_weights[q.source][asset_type]
        freshness = {"live": 1.0, "delayed": 0.8, "eod": 0.6}.get(q.freshness_status, 0.5)
        market_time_bonus = 0.1 if q.market_time else 0.0
        primary_bonus = 1.2 if q.source == primary_provider else 1.0
        fallback_penalty = 0.5 if q.is_fallback else 1.0
        weight = base * freshness * primary_bonus * fallback_penalty + market_time_bonus
        weighted_sum += weight
        total_weight += base  # denominator uses base weights only
    return min(weighted_sum / total_weight, 1.0) if total_weight > 0 else 0.0
```

---

## 5. Outlier Thresholds (YAML config)

```yaml
outlier_thresholds:
  index:      0.01    # 1%
  stock:      0.02    # 2%
  forex:      0.005   # 0.5%
  crypto:     0.05    # 5%
  commodity:  0.03    # 3%
  bond:       0.01    # 1%
  volatility: 0.05    # 5%
```

These values live in `market_data_config.yaml` and are loaded by ConsensusEngine at init. Changing them requires no code change.

---

## 6. Provider Weights (YAML config)

```yaml
provider_weights:
  stooq:
    index: 0.9
    stock: 0.5
    bond: 0.8
    volatility: 0.8
    forex: 0.4
    crypto: 0.0
    commodity: 0.5
  finnhub:
    index: 0.7
    stock: 0.9
    forex: 0.6
    crypto: 0.85
    commodity: 0.3
    bond: 0.3
    volatility: 0.3
  twelvedata:
    index: 0.8
    stock: 0.75
    forex: 0.9
    crypto: 0.7
    commodity: 0.8
    bond: 0.5
    volatility: 0.5
  alphavantage:
    index: 0.6
    stock: 0.65
    forex: 0.7
    crypto: 0.6
    commodity: 0.4
    bond: 0.3
    volatility: 0.3
  fmp:
    index: 0.5
    stock: 0.7
    forex: 0.3
    crypto: 0.3
    commodity: 0.3
    bond: 0.3
    volatility: 0.2
  yahoo:
    index: 0.3
    stock: 0.3
    forex: 0.3
    crypto: 0.3
    commodity: 0.3
    bond: 0.3
    volatility: 0.3
```

---

## 7. RequestBudget (`budget.py`)

```python
class RequestBudget:
    """Daily per-provider request counter backed by DuckDB log."""

    def can_request(self, provider: str) -> bool:
        """Return True if provider has remaining budget for today."""

    def record_request(self, provider: str) -> None:
        """Increment today's count for provider."""

    def get_remaining(self, provider: str) -> int:
        """Return estimated remaining requests for today."""
```

**Budget limits (conservative):**

| Provider | Free tier limit | Budget limit |
|---|---|---|
| Alpha Vantage | 500/day | 400/day |
| TwelveData | 800/day | 700/day |
| FMP | 250/day | 200/day |
| Finnhub | 60/min | tracked per minute |
| Stooq | unlimited | — |
| Yahoo | unlimited | — |

When `can_request()` returns False:
- Provider is skipped in the parallel fetch
- Warning `budget_exhausted` is added to the quote

Budget counts are stored in `market_provider_logs` (existing DuckDB table) by querying `COUNT(*) WHERE provider=? AND fetched_at >= today`.

---

## 8. Normalized Warning Codes

All warnings in `MarketQuoteInternal.warning` and `ConsensusResult.warnings` use these codes:

| Code | Meaning |
|---|---|
| `rate_limited` | Provider returned 429 or rate limit signal |
| `budget_exhausted` | Daily budget for this provider is consumed |
| `provider_error` | Provider returned an error response |
| `provider_timeout` | Provider request timed out |
| `provider_mismatch` | Primary provider price deviates from consensus median |
| `outlier_detected` | One or more providers discarded as price outliers |
| `unverified_single_provider` | Only one provider returned valid data |
| `yahoo_last_resort` | Yahoo used because all other providers failed |
| `stale_cache_used` | Cached data returned because all providers failed |

---

## 9. Structured Decision Log

Every quote resolution emits a structured log entry at DEBUG level:

```python
logger.debug("consensus_decision", extra={
    "internal_symbol": asset.internal_symbol,
    "selected_source": result.selected_source,
    "consensus_method": result.consensus_method,
    "consensus_price": result.consensus_price,
    "provider_count": result.provider_count,
    "valid_provider_count": result.valid_provider_count,
    "outliers": result.outliers,
    "discarded_providers": result.discarded_providers,
    "warnings": result.warnings,
    "confidence_score": result.confidence_score,
    "reason": result.reason,
})
```

---

## 10. ProviderRouter changes

- **Parallel fetch:** use `concurrent.futures.ThreadPoolExecutor` to fetch all providers simultaneously. Timeout per provider: 5s (configurable).
- **Yahoo guard:** Yahoo is only added to the fetch pool if `valid_provider_count == 0` after all others complete.
- **Budget check:** Before dispatching each provider, call `budget.can_request(provider)`. Skip if False.
- **Result:** Pass all collected quotes to `ConsensusEngine.resolve()`. Store the result in cache as before.

---

## 11. TwelveDataProvider

- Endpoint: `https://api.twelvedata.com/price` and `/quote`
- Auth: `apikey` query param
- Free tier symbols: stocks (US + major EU exchanges), forex, crypto, indices, commodities
- `supports()`: returns True for all asset types except `fundamentals`
- Rate: 8 req/min, 800/day → enforced via `RequestBudget`

---

## 12. What does NOT change

- `MarketQuoteInternal` dataclass — no new required fields
- `/api/markets/quotes` response schema — `QuoteOut` unchanged
- `cache.py` — no changes
- All 35 existing unit tests must pass without modification
- `stooq` provider code — unchanged (already handles its own errors gracefully)

---

## 13. Testing strategy

| Test | Type |
|---|---|
| `test_consensus_primary_wins` | Unit — primary within threshold, use primary |
| `test_consensus_median_on_mismatch` | Unit — primary deviates, fall back to median |
| `test_consensus_outlier_discarded` | Unit — outlier removed, median recalculated |
| `test_consensus_single_provider` | Unit — 1 valid → unverified warning, confidence ≤ 0.6 |
| `test_consensus_no_providers` | Unit — 0 valid → error quote |
| `test_budget_skip_when_exhausted` | Unit — AV skipped when budget exceeded |
| `test_twelvedata_provider_quote` | Unit (mocked HTTP) — valid response parsed correctly |
| `test_router_parallel_fetch` | Integration (mocked providers) — all called in parallel |
| `test_yahoo_only_as_last_resort` | Integration — Yahoo not called if any other provider succeeds |
