from datetime import datetime
from pathlib import Path
from typing import List

from models.evaluation import CoverageReport, ProviderEvaluation

_OUTPUT_DIR = Path(__file__).parent.parent / "output" / "reports"


def generate_report(report: CoverageReport, timestamp: str | None = None) -> Path:
    """
    Generate a Markdown report at output/reports/{timestamp}_report.md.

    Returns the path of the written file.
    """
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = timestamp or datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    path = _OUTPUT_DIR / f"{ts}_report.md"

    lines: List[str] = []

    # --- Executive Summary ---
    lines.append("# Market Data POC — Evaluation Report\n")
    lines.append(f"**Generated:** {datetime.utcnow().isoformat()}Z\n")
    lines.append("## Executive Summary\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total providers tested | {report.total_providers} |")
    lines.append(f"| Successful | {report.successful} |")
    lines.append(f"| Failed | {report.failed} |")
    lines.append(f"| Unavailable (no API key) | {report.unavailable} |")
    lines.append(f"| Total elapsed time | {report.total_time_ms / 1000:.1f}s |")
    lines.append("")

    # --- Coverage by Region ---
    lines.append("## Coverage by Region\n")
    lines.append("| Region | Providers | Successful |")
    lines.append("|--------|-----------|------------|")
    for region, evals in sorted(report.by_region.items()):
        successful = sum(1 for e in evals if e.adapter_result.success)
        lines.append(f"| {region} | {len(evals)} | {successful} |")
    lines.append("")

    # --- Coverage by Category ---
    lines.append("## Coverage by Category\n")
    lines.append("| Category | Providers | Successful |")
    lines.append("|----------|-----------|------------|")
    for category, evals in sorted(report.by_category.items()):
        successful = sum(1 for e in evals if e.adapter_result.success)
        lines.append(f"| {category} | {len(evals)} | {successful} |")
    lines.append("")

    # --- Provider Ranking ---
    lines.append("## Provider Ranking\n")
    lines.append("| # | Provider | Score | Quality | Reliability | Coverage | Recommendation |")
    lines.append("|---|----------|-------|---------|-------------|----------|----------------|")
    sorted_evals = sorted(report.evaluations, key=lambda e: e.score_total, reverse=True)
    for i, ev in enumerate(sorted_evals, start=1):
        lines.append(
            f"| {i} | {ev.provider} | {ev.score_total:.1f} | {ev.data_quality:.1f} "
            f"| {ev.reliability:.1f} | {ev.coverage_breadth:.1f} | {ev.recommendation} |"
        )
    lines.append("")

    # --- Best Provider by Asset Type ---
    lines.append("## Best Provider by Asset Type\n")
    asset_types = {
        "macro": "macro",
        "markets": "markets",
        "companies": "companies",
        "news": "news",
    }
    for asset_type, category_key in asset_types.items():
        candidates = report.by_category.get(category_key, [])
        if candidates:
            best = max(candidates, key=lambda e: e.score_total)
            lines.append(f"- **{asset_type.capitalize()}:** {best.provider} (score {best.score_total:.1f})")
    lines.append("")

    # --- Detected Limitations ---
    lines.append("## Detected Limitations\n")
    failed_providers = [
        e.provider for e in report.evaluations if not e.adapter_result.success
    ]
    if failed_providers:
        lines.append("Providers that failed or returned no data:\n")
        for p in failed_providers:
            lines.append(f"- {p}")
    else:
        lines.append("No critical failures detected.")
    lines.append("")

    freemium_providers = [
        e.provider for e in report.evaluations
        if e.adapter_result.metadata.license == "freemium"
    ]
    if freemium_providers:
        lines.append("\nProviders requiring API key (freemium):\n")
        for p in freemium_providers:
            lines.append(f"- {p}")
    lines.append("")

    # --- Final Recommendations ---
    lines.append("## Final Recommendations\n")
    principals = [e for e in sorted_evals if e.recommendation == "principal"]
    secundarios = [e for e in sorted_evals if e.recommendation == "secundario"]
    fallbacks = [e for e in sorted_evals if e.recommendation == "fallback"]
    descartados = [e for e in sorted_evals if e.recommendation == "descartado"]

    if principals:
        lines.append("### Principal (score >= 75)\n")
        for e in principals:
            lines.append(f"- **{e.provider}** — {e.score_total:.1f} pts")
    if secundarios:
        lines.append("\n### Secundario (50–74)\n")
        for e in secundarios:
            lines.append(f"- {e.provider} — {e.score_total:.1f} pts")
    if fallbacks:
        lines.append("\n### Fallback (30–49)\n")
        for e in fallbacks:
            lines.append(f"- {e.provider} — {e.score_total:.1f} pts")
    if descartados:
        lines.append("\n### Descartado (< 30)\n")
        for e in descartados:
            lines.append(f"- {e.provider} — {e.score_total:.1f} pts")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    return path
