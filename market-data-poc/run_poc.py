"""
run_poc.py — Market Data POC entry point.

Usage:
    python run_poc.py [--providers all|spain|europe|usa|global] \
                      [--output json,csv,report,catalog] \
                      [--timeout 10] \
                      [--workers 5]
"""

import argparse
import importlib
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List

import yaml
from rich.console import Console
from rich.table import Table

# Ensure project root is on sys.path so sibling packages resolve correctly
sys.path.insert(0, str(Path(__file__).parent))

from adapters.base import BaseAdapter
from models.base import AdapterResult
from models.evaluation import CoverageReport, ProviderEvaluation
from services.runner import run_adapters
from services.scorer import score_adapter
from services.cache import LocalTTLCache
from services.comparator import compare_equivalent_values
from services.orchestrator import ProviderOrchestrator
from validators.data_quality import validate_records

console = Console()

# Map CLI filter -> provider regions in providers.yaml
_REGION_FILTERS = {
    "spain": {"spain"},
    "europe": {"eurozone", "europe"},
    "usa": {"usa"},
    "global": {"global"},
    "all": None,  # None means no filter
}

# Map provider id -> adapter module path (adapters/<subpkg>/<id>.py)
_ADAPTER_MAP = {
    # Spain
    "bde": "adapters.spain.bde",
    "ine": "adapters.spain.ine",
    "cnmv": "adapters.spain.cnmv",
    "bme": "adapters.spain.bme",
    "tesoro": "adapters.spain.tesoro",
    "ree": "adapters.spain.ree",
    "aemet": "adapters.spain.aemet",
    "seguridad_social": "adapters.spain.seguridad_social",
    "agencia_tributaria": "adapters.spain.agencia_tributaria",
    # Europe
    "ecb": "adapters.europe.ecb",
    "eurostat": "adapters.europe.eurostat",
    "oecd": "adapters.europe.oecd",
    "bis": "adapters.europe.bis",
    "european_commission": "adapters.europe.european_commission",
    "eur_lex": "adapters.europe.eur_lex",
    # USA
    "fred": "adapters.usa.fred",
    "edgar": "adapters.usa.edgar",
    "bls": "adapters.usa.bls",
    "treasury": "adapters.usa.treasury",
    "bea": "adapters.usa.bea",
    "census": "adapters.usa.census",
    "eia": "adapters.usa.eia",
    # Global
    "world_bank": "adapters.global_.world_bank",
    "imf": "adapters.global_.imf",
    "coingecko": "adapters.global_.coingecko",
    "stooq": "adapters.global_.stooq",
    "alpha_vantage": "adapters.global_.alpha_vantage",
    "finnhub": "adapters.global_.finnhub",
    "fmp": "adapters.global_.fmp",
    "twelvedata": "adapters.global_.twelvedata",
    "openfigi": "adapters.global_.openfigi",
    "opencorporates": "adapters.global_.opencorporates",
    "polygon": "adapters.global_.polygon",
    "un_data": "adapters.global_.un_data",
    # RSS
    "rss": "adapters.rss.reader",
}

_EXTRA_PROVIDERS = [
    {"name": "AEMET", "id": "aemet", "category": "macro", "region": "Spain", "capabilities": ["macro", "economic_calendar"]},
    {"name": "Seguridad Social", "id": "seguridad_social", "category": "macro", "region": "Spain", "capabilities": ["macro", "employment", "historical"]},
    {"name": "Agencia Tributaria", "id": "agencia_tributaria", "category": "macro", "region": "Spain", "capabilities": ["macro", "tax", "historical"]},
    {"name": "BIS", "id": "bis", "category": "macro", "region": "Global", "capabilities": ["macro", "bonds", "currency", "historical"]},
    {"name": "European Commission Data", "id": "european_commission", "category": "macro", "region": "Europe", "capabilities": ["macro", "economic_calendar", "historical"]},
    {"name": "EUR-Lex", "id": "eur_lex", "category": "macro", "region": "Europe", "capabilities": ["macro", "news", "regulatory"]},
    {"name": "BEA", "id": "bea", "category": "macro", "region": "USA", "capabilities": ["macro", "gdp", "historical"]},
    {"name": "Census Bureau", "id": "census", "category": "macro", "region": "USA", "capabilities": ["macro", "housing", "retail", "historical"]},
    {"name": "EIA", "id": "eia", "category": "macro", "region": "USA", "capabilities": ["macro", "commodities", "energy", "historical"]},
    {"name": "OpenFIGI", "id": "openfigi", "category": "companies", "region": "Global", "capabilities": ["stocks", "etf", "funds", "isin"]},
    {"name": "OpenCorporates", "id": "opencorporates", "category": "companies", "region": "Global", "capabilities": ["companies", "corporate_actions"]},
    {"name": "Polygon", "id": "polygon", "category": "markets", "region": "Global", "capabilities": ["stocks", "etf", "forex", "crypto", "dividends", "earnings", "intraday", "realtime"]},
    {"name": "UN Data", "id": "un_data", "category": "macro", "region": "Global", "capabilities": ["macro", "historical"]},
]


def load_providers_yaml() -> list:
    yaml_path = Path(__file__).parent / "config" / "providers.yaml"
    with open(yaml_path, encoding="utf-8") as fh:
        providers = yaml.safe_load(fh)
    existing = {provider["id"] for provider in providers}
    providers.extend(provider for provider in _EXTRA_PROVIDERS if provider["id"] not in existing)
    return providers


def load_adapters(provider_ids: List[str], provider_catalog: list | None = None) -> List[BaseAdapter]:
    """Dynamically import and instantiate adapters for the given provider IDs."""
    adapters: List[BaseAdapter] = []
    provider_config = {provider["id"]: provider for provider in provider_catalog or []}
    for pid in provider_ids:
        module_path = _ADAPTER_MAP.get(pid)
        if not module_path:
            console.print(f"[yellow]No adapter registered for provider id '{pid}' — skipping[/yellow]")
            continue
        try:
            module = importlib.import_module(module_path)
            adapter_cls = getattr(module, "Adapter", None)
            if adapter_cls is None:
                candidates = [
                    value
                    for value in vars(module).values()
                    if isinstance(value, type)
                    and issubclass(value, BaseAdapter)
                    and value is not BaseAdapter
                ]
                adapter_cls = candidates[0] if candidates else None
            if adapter_cls is None:
                console.print(
                    f"[yellow]Module '{module_path}' has no BaseAdapter implementation - skipping '{pid}'[/yellow]"
                )
                continue
            adapter = adapter_cls()
            config = provider_config.get(pid, {})
            capabilities = config.get("capabilities") or [config.get("category", "")]
            adapter.capabilities = tuple(cap for cap in capabilities if cap)
            if config.get("priority"):
                adapter.priority = config["priority"]
            adapters.append(adapter)
        except ModuleNotFoundError:
            console.print(f"[yellow]Adapter module '{module_path}' not found — skipping '{pid}'[/yellow]")
        except Exception as exc:
            console.print(f"[red]Error loading adapter '{pid}': {exc}[/red]")
    return adapters


def filter_providers(providers: list, region_filter: str) -> list:
    regions = _REGION_FILTERS.get(region_filter.lower())
    if regions is None:
        return providers  # "all"
    selected = [p for p in providers if p.get("region", "").lower() in regions]
    if region_filter.lower() == "europe":
        selected.extend(p for p in providers if p.get("id") == "oecd" and p not in selected)
    return selected


def build_coverage_report(
    evaluations: List[ProviderEvaluation],
    unavailable_count: int,
    total_time_ms: float,
) -> CoverageReport:
    successful = sum(1 for e in evaluations if e.adapter_result.success)
    failed = len(evaluations) - successful

    by_region: dict = {}
    by_category: dict = {}
    for ev in evaluations:
        region = ev.adapter_result.metadata.region
        by_region.setdefault(region, []).append(ev)
        category = ev.adapter_result.metadata.category
        by_category.setdefault(category, []).append(ev)

    return CoverageReport(
        total_providers=len(evaluations) + unavailable_count,
        successful=successful,
        failed=failed,
        unavailable=unavailable_count,
        evaluations=evaluations,
        by_region=by_region,
        by_category=by_category,
        total_time_ms=total_time_ms,
    )


def print_summary_table(report: CoverageReport) -> None:
    table = Table(title="Provider Evaluation Summary", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Provider", style="bold")
    table.add_column("Score", justify="right")
    table.add_column("Quality", justify="right")
    table.add_column("Reliability", justify="right")
    table.add_column("Recommendation", style="cyan")

    sorted_evals = sorted(report.evaluations, key=lambda e: e.score_total, reverse=True)
    for i, ev in enumerate(sorted_evals, start=1):
        rec_color = {
            "principal": "green",
            "secundario": "yellow",
            "fallback": "orange1",
            "descartado": "red",
        }.get(ev.recommendation, "white")
        table.add_row(
            str(i),
            ev.provider,
            f"{ev.score_total:.1f}",
            f"{ev.data_quality:.1f}",
            f"{ev.reliability:.1f}",
            f"[{rec_color}]{ev.recommendation}[/{rec_color}]",
        )

    console.print(table)
    console.print(
        f"\n[bold]Tested:[/bold] {report.total_providers} | "
        f"[green]OK: {report.successful}[/green] | "
        f"[red]Failed: {report.failed}[/red] | "
        f"[yellow]Unavailable: {report.unavailable}[/yellow] | "
        f"Time: {report.total_time_ms / 1000:.1f}s"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Market Data POC — evaluate financial data providers"
    )
    parser.add_argument(
        "--providers",
        default="all",
        choices=["all", "spain", "europe", "usa", "global"],
        help="Filter providers by region (default: all)",
    )
    parser.add_argument(
        "--output",
        default="json,csv,report,catalog",
        help="Comma-separated export formats: json, csv, report, catalog (default: json,csv,report,catalog)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Per-adapter timeout in seconds (default: 10)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="Number of concurrent workers (default: 5)",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="market:poc",
        choices=[
            "market:poc",
            "market:health",
            "market:coverage",
            "market:providers",
            "market:compare",
            "market:report",
            "market:cache:clear",
            "market:test",
        ],
        help="POC command to run",
    )
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=900,
        help="Local cache TTL in seconds (default: 900)",
    )
    args = parser.parse_args()

    output_formats = {fmt.strip().lower() for fmt in args.output.split(",")}
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

    console.print(f"[bold blue]Market Data POC[/bold blue] — region: [cyan]{args.providers}[/cyan]")

    # 1. Load providers catalog
    all_providers = load_providers_yaml()
    selected_providers = filter_providers(all_providers, args.providers)
    console.print(f"Providers in catalog: {len(selected_providers)}")

    # 2. Load adapters
    provider_ids = [p["id"] for p in selected_providers]
    adapters = load_adapters(provider_ids, selected_providers)

    if args.command == "market:providers":
        table = Table(title="Provider Catalog", show_lines=True)
        table.add_column("ID")
        table.add_column("Name")
        table.add_column("Region")
        table.add_column("Category")
        table.add_column("Capabilities")
        for provider in selected_providers:
            table.add_row(
                provider["id"],
                provider["name"],
                provider.get("region", ""),
                provider.get("category", ""),
                ", ".join(provider.get("capabilities", [])),
            )
        console.print(table)
        return

    cache = LocalTTLCache(ttl_seconds=args.cache_ttl)
    if args.command == "market:cache:clear":
        cleared = cache.clear()
        console.print(f"[green]Cleared {cleared} cache files[/green]")
        return

    # 3. Filter unavailable adapters (no API key)
    available: List[BaseAdapter] = []
    unavailable_count = 0
    for adapter in adapters:
        if adapter.is_available():
            available.append(adapter)
        else:
            console.print(
                f"[yellow]Skipping '{adapter.name}' — requires API key not found in environment[/yellow]"
            )
            unavailable_count += 1

    console.print(f"Running {len(available)} adapters ({unavailable_count} skipped)...\n")

    orchestrator = ProviderOrchestrator(available, cache=cache)
    if args.command == "market:health":
        table = Table(title="Provider Health", show_lines=True)
        table.add_column("Provider")
        table.add_column("Status")
        table.add_column("Latency", justify="right")
        table.add_column("Error")
        for health in orchestrator.health():
            table.add_row(
                health.provider,
                health.status.value,
                f"{health.latency_ms:.0f} ms",
                health.error or "",
            )
        console.print(table)
        return

    # 4. Run
    t0 = time.perf_counter()
    results: List[AdapterResult] = run_adapters(
        available, max_workers=args.workers, timeout=args.timeout
    )
    total_time_ms = (time.perf_counter() - t0) * 1000

    # 5. Validate records
    for result in results:
        if result.records:
            result.records = validate_records(result.records)

    # 6. Score
    evaluations: List[ProviderEvaluation] = [score_adapter(r) for r in results]

    # 7. Build coverage report
    coverage = build_coverage_report(evaluations, unavailable_count, total_time_ms)

    if args.command == "market:compare":
        metrics = compare_equivalent_values(results)
        table = Table(title="Provider Comparison", show_lines=True)
        table.add_column("Key")
        table.add_column("Providers")
        table.add_column("Spread")
        table.add_column("Spread %")
        for metric in metrics:
            table.add_row(
                metric.key,
                ", ".join(metric.providers),
                f"{metric.spread_abs:.4f}",
                f"{metric.spread_pct:.2f}%",
            )
        console.print(table)
        return

    # 8. Export
    if "json" in output_formats:
        from exporters.json_exporter import export_results
        paths = export_results(results, timestamp)
        console.print(f"[green]JSON:[/green] {len(paths)} files written to output/json/")

    if "csv" in output_formats:
        from exporters.csv_exporter import export_records
        csv_path = export_records(results, timestamp)
        console.print(f"[green]CSV:[/green] {csv_path}")

    if "report" in output_formats:
        from exporters.report_generator import generate_report
        report_path = generate_report(coverage, timestamp)
        console.print(f"[green]Report:[/green] {report_path}")

    if "catalog" in output_formats:
        from exporters.catalog_generator import generate_catalog
        catalog_paths = generate_catalog(coverage, timestamp)
        console.print(f"[green]Catalog:[/green] {catalog_paths['markdown']}")

    # 9. Print summary table
    print_summary_table(coverage)


if __name__ == "__main__":
    main()
