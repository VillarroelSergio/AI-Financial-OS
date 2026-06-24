"""ConsensusEngine — resolves price from multiple provider quotes.

Strategy: D (primary + validation) + B (median for discrepancies) + C (weighted confidence).

Decision flow:
  0 valid  → error
  1 valid  → unverified_single_provider, confidence *= 0.6
  ≥2 valid → median (if ≥3: remove outliers first), primary vs median check,
             weighted confidence score
"""
from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from app.modules.investments.market_data.providers.base import MarketQuoteInternal

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent / "config" / "market_data_config.yaml"

# Threshold for "primary agrees with median" check (fixed, not per-asset)
_PRIMARY_AGREE_THRESHOLD = 0.01  # 1%

_FRESHNESS_FACTOR: dict[str, float] = {
    "live": 1.0,
    "fresh": 0.9,
    "delayed": 0.8,
    "eod": 0.6,
    "closed": 0.6,
    "unknown": 0.5,
    "stale": 0.3,
    "error": 0.0,
}


@dataclass
class ConsensusResult:
    price: Optional[float]
    confidence_score: float
    selected_source: str
    consensus_method: str          # "primary" | "median" | "single" | "error"
    consensus_price: Optional[float]
    provider_count: int
    valid_provider_count: int
    outliers: list[str] = field(default_factory=list)
    discarded_providers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    reason: str = ""
    freshness_status: str = "unknown"
    source_type: str = "unknown"


class ConsensusEngine:
    """Resolves the best price from a list of provider quotes."""

    def __init__(self) -> None:
        cfg = yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8"))
        self._outlier_thresholds: dict[str, float] = cfg.get("outlier_thresholds", {})
        self._provider_weights: dict[str, dict[str, float]] = cfg.get("provider_weights", {})

    def resolve(
        self,
        quotes: list[MarketQuoteInternal],
        asset_type: str,
        primary_provider: str,
    ) -> ConsensusResult:
        provider_count = len(quotes)
        valid = [q for q in quotes if q.price is not None and q.freshness_status != "error"]
        valid_provider_count = len(valid)

        # Case 0: no valid data
        if valid_provider_count == 0:
            return ConsensusResult(
                price=None,
                confidence_score=0.0,
                selected_source="none",
                consensus_method="error",
                consensus_price=None,
                provider_count=provider_count,
                valid_provider_count=0,
                warnings=["provider_error"],
                reason="No providers returned valid price data",
            )

        # Case 1: single valid provider
        if valid_provider_count == 1:
            q = valid[0]
            base_conf = self._base_weight(q.source, asset_type)
            return ConsensusResult(
                price=q.price,
                confidence_score=min(base_conf * 0.6, 0.6),
                selected_source=q.source,
                consensus_method="single",
                consensus_price=q.price,
                provider_count=provider_count,
                valid_provider_count=1,
                warnings=["unverified_single_provider"],
                reason=f"Only {q.source} returned valid data; result unverified",
                freshness_status=q.freshness_status,
                source_type=q.source_type,
            )

        # Case 2+: multiple valid providers
        outliers: list[str] = []
        discarded: list[str] = []
        warnings: list[str] = []

        prices = [q.price for q in valid]

        if valid_provider_count >= 3:
            threshold = self._outlier_thresholds.get(asset_type, 0.02)
            median_all = statistics.median(prices)
            clean = []
            for q in valid:
                deviation = abs(q.price - median_all) / median_all if median_all else 0
                if deviation > threshold:
                    outliers.append(q.source)
                    discarded.append(q.source)
                else:
                    clean.append(q)
            if outliers:
                warnings.append("outlier_detected")
            valid = clean if clean else valid  # don't discard all
            prices = [q.price for q in valid]

        consensus_price = statistics.median(prices)

        # Check primary provider
        primary_quote: Optional[MarketQuoteInternal] = next(
            (q for q in valid if q.source == primary_provider), None
        )

        if primary_quote is not None:
            deviation = abs(primary_quote.price - consensus_price) / consensus_price if consensus_price else 0
            if deviation <= _PRIMARY_AGREE_THRESHOLD:
                selected_price = primary_quote.price
                selected_source = primary_provider
                method = "primary"
                reason = (
                    f"Primary ({primary_provider}) agrees with median "
                    f"(diff={deviation*100:.2f}%)"
                )
            else:
                selected_price = consensus_price
                selected_source = "consensus_median"
                method = "median"
                warnings.append("provider_mismatch")
                reason = (
                    f"Primary ({primary_provider}) deviates {deviation*100:.2f}% from median; "
                    f"using median of {[q.source for q in valid]}"
                )
        else:
            selected_price = consensus_price
            selected_source = "consensus_median"
            method = "median"
            # Only emit provider_mismatch if primary was discarded as outlier
            if primary_provider in discarded:
                warnings.append("provider_mismatch")
                reason = f"Primary provider {primary_provider} discarded as outlier; using median"
            else:
                reason = f"Primary provider {primary_provider} not in valid set; using median"

        confidence = self._weighted_confidence(valid, asset_type, primary_provider)

        # Pick representative freshness from best available quote
        freshness = max(
            (q.freshness_status for q in valid),
            key=lambda s: _FRESHNESS_FACTOR.get(s, 0),
        )

        return ConsensusResult(
            price=selected_price,
            confidence_score=confidence,
            selected_source=selected_source,
            consensus_method=method,
            consensus_price=consensus_price,
            provider_count=provider_count,
            valid_provider_count=len(valid),
            outliers=outliers,
            discarded_providers=discarded,
            warnings=warnings,
            reason=reason,
            freshness_status=freshness,
            source_type="consensus" if method == "median" else (primary_quote.source_type if primary_quote else "unknown"),
        )

    def _base_weight(self, provider: str, asset_type: str) -> float:
        return self._provider_weights.get(provider, {}).get(asset_type, 0.5)

    def _weighted_confidence(
        self,
        quotes: list[MarketQuoteInternal],
        asset_type: str,
        primary_provider: str,
    ) -> float:
        total_base = 0.0
        weighted_sum = 0.0
        for q in quotes:
            base = self._base_weight(q.source, asset_type)
            freshness = _FRESHNESS_FACTOR.get(q.freshness_status, 0.5)
            market_time_bonus = 0.1 if q.market_time else 0.0
            primary_bonus = 1.2 if q.source == primary_provider else 1.0
            fallback_penalty = 0.5 if q.is_fallback else 1.0
            weight = base * freshness * primary_bonus * fallback_penalty + market_time_bonus
            weighted_sum += weight
            total_base += base
        if total_base == 0:
            return 0.0
        return min(weighted_sum / total_base, 1.0)
