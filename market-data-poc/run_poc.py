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
from catalog import CatalogLoader
from models.base import AdapterResult
from models.catalog import CatalogIndicator, CatalogFetchResult
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
    "frankfurter": "adapters.global_.frankfurter",
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
    {"name": "Frankfurter", "id": "frankfurter", "category": "markets", "region": "Global", "capabilities": ["currency", "forex", "historical"], "priority": "primary"},
    {"name": "UN Data", "id": "un_data", "category": "macro", "region": "Global", "capabilities": ["macro", "historical"]},
]

_COMMAND_PROVIDER_IDS = {
    "market:currency": {"ecb", "polygon", "frankfurter"},
    "market:bonds": {"treasury", "fred", "bde", "tesoro", "bis"},
    "market:stabilize": {
        "ecb", "polygon", "frankfurter", "treasury", "fred", "bde", "tesoro",
        "cnmv", "eurostat", "agencia_tributaria", "bis", "opencorporates",
    },
}

_CAPABILITY_MODELS = {
    "currency": {"Currency", "CurrencyRate"},
    "forex": {"Currency", "CurrencyRate"},
    "bonds": {"YieldCurve", "YieldCurvePoint", "BondYield"},
}


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


def _capability_status(report: CoverageReport) -> dict[str, dict[str, list[str]]]:
    status: dict[str, dict[str, list[str]]] = {}
    for ev in report.evaluations:
        provider = ev.provider
        capabilities = getattr(ev.adapter_result.metadata, "capabilities", ()) or ()
        record_models = {record.__class__.__name__ for record in ev.adapter_result.records}
        for capability in capabilities:
            item = status.setdefault(
                capability,
                {"declared": [], "collected": [], "failed": [], "api_key": []},
            )
            item["declared"].append(provider)
            expected_models = _CAPABILITY_MODELS.get(capability)
            collected = ev.adapter_result.success and (
                not expected_models or bool(record_models & expected_models)
            )
            if collected:
                item["collected"].append(provider)
            elif ev.adapter_result.metadata.requires_api_key:
                item["api_key"].append(provider)
            else:
                item["failed"].append(provider)
    return status


def print_gap_table(report: CoverageReport, timestamp: str | None = None) -> Path:
    expected = ("currency", "bonds")
    status = _capability_status(report)
    output_dir = Path(__file__).parent / "output" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{timestamp or datetime.utcnow().strftime('%Y%m%dT%H%M%S')}_gap_report.md"
    lines = [
        "# Market Data POC - Gap Report",
        "",
        "| Gap | Estado | Proveedores candidatos | Proveedor principal recomendado | Fallback | Accion tecnica pendiente | Bloqueante para BBDD |",
        "|-----|--------|-------------------------|--------------------------------|----------|--------------------------|----------------------|",
    ]
    table = Table(title="Real Capability Gaps", show_lines=True)
    table.add_column("Gap")
    table.add_column("Status")
    table.add_column("Collected")
    table.add_column("Failed/API key")
    for gap in expected:
        item = status.get(gap, {"declared": [], "collected": [], "failed": [], "api_key": []})
        collected = sorted(set(item["collected"]))
        failed = sorted(set(item["failed"]))
        api_key = sorted(set(item["api_key"]))
        state = "ok" if collected else ("api_key" if api_key and not failed else "failed")
        recommended = collected[0] if collected else (api_key[0] if api_key else "")
        fallback = ", ".join(collected[1:] or api_key or failed)
        action = "Ninguna" if collected else "Corregir parser/endpoints o configurar API key opcional"
        blocking = "no" if collected else "si"
        table.add_row(gap, state, ", ".join(collected), ", ".join(failed + api_key))
        lines.append(
            f"| {gap} | {state} | {', '.join(sorted(set(item['declared'])))} | {recommended} | {fallback} | {action} | {blocking} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    console.print(table)
    console.print(f"[green]Gap report:[/green] {path}")
    return path


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


def cmd_catalog_show(loader: CatalogLoader) -> None:
    table = Table(title="Market Data Catalog", show_lines=True)
    table.add_column("ID", style="bold")
    table.add_column("Name")
    table.add_column("Priority")
    table.add_column("Freq")
    table.add_column("Dash")
    table.add_column("AI")
    table.add_column("Primary")
    table.add_column("Secondary")
    table.add_column("Fallback")
    for ind in loader.load_all():
        priority_color = {
            "critical": "red", "high": "yellow",
            "medium": "cyan", "low": "dim",
        }.get(ind.priority, "white")
        table.add_row(
            ind.id, ind.name,
            f"[{priority_color}]{ind.priority}[/{priority_color}]",
            ind.frequency,
            "Y" if ind.dashboard else "",
            "Y" if ind.ai else "",
            ind.provider_primary,
            ind.provider_secondary or "",
            ind.provider_fallback or "",
        )
    console.print(table)
    indicators = loader.load_all()
    console.print(f"\nTotal: {len(indicators)} indicators | "
                  f"Critical: {sum(1 for i in indicators if i.priority=='critical')} | "
                  f"High: {sum(1 for i in indicators if i.priority=='high')} | "
                  f"Dashboard: {sum(1 for i in indicators if i.dashboard)} | "
                  f"AI: {sum(1 for i in indicators if i.ai)}")


def cmd_catalog_validate(loader: CatalogLoader) -> bool:
    errors = loader.validate()
    if not errors:
        console.print("[green]OK Catalog valid — no errors found[/green]")
        console.print(f"  {len(loader.load_all())} indicators loaded from catalog/")
        return True
    console.print(f"[red]ERROR Catalog has {len(errors)} error(s):[/red]")
    for err in errors:
        console.print(f"  [red]• {err}[/red]")
    return False


def cmd_catalog_list(loader: CatalogLoader, priority: str | None, category: str | None) -> None:
    indicators = loader.load_all()
    if priority:
        indicators = [i for i in indicators if i.priority == priority]
    if category:
        indicators = [i for i in indicators if i.category == category]
    table = Table(title=f"Catalog — priority={priority or 'all'} category={category or 'all'}", show_lines=True)
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Priority")
    table.add_column("Category")
    table.add_column("Freq")
    table.add_column("Provider")
    for ind in indicators:
        table.add_row(ind.id, ind.name, ind.priority, ind.category, ind.frequency, ind.provider_primary)
    console.print(table)
    console.print(f"Total: {len(indicators)}")


def cmd_catalog_coverage(loader: CatalogLoader, adapters: list) -> None:
    from services.orchestrator import ProviderOrchestrator
    orch = ProviderOrchestrator(adapters)
    indicators = loader.load_all()
    table = Table(title="Catalog Coverage", show_lines=True)
    table.add_column("ID")
    table.add_column("Priority")
    table.add_column("Primary")
    table.add_column("Migrated?")
    table.add_column("Secondary")
    table.add_column("Fallback")
    migrated = 0
    for ind in indicators:
        adapter = orch._get_adapter(ind.provider_primary)
        is_migrated = adapter is not None and adapter.supports(ind.id)
        if is_migrated:
            migrated += 1
        table.add_row(
            ind.id, ind.priority, ind.provider_primary,
            "[green]YES[/green]" if is_migrated else "[red]NO[/red]",
            ind.provider_secondary or "",
            ind.provider_fallback or "",
        )
    console.print(table)
    console.print(f"\nMigrated: {migrated}/{len(indicators)} indicators have a migrated primary provider")


def cmd_market_update(loader: CatalogLoader, adapters: list, timestamp: str, output_formats: set) -> None:
    from services.orchestrator import ProviderOrchestrator
    from exporters.csv_exporter import export_catalog_results
    orch = ProviderOrchestrator(adapters)
    indicators = loader.get_by_priority("critical", "high")
    console.print(f"Fetching {len(indicators)} indicators (critical + high priority)...")
    results: list[CatalogFetchResult] = []
    for ind in indicators:
        console.print(f"  [{ind.priority}] {ind.id} ...", end="")
        cfr = orch.fetch_indicator(ind)
        results.append(cfr)
        status = "[green]OK[/green]" if cfr.adapter_result.success else "[red]FAIL[/red]"
        provider = cfr.provider_used
        console.print(f" {status} ({provider})")
    successful = sum(1 for r in results if r.adapter_result.success)
    console.print(f"\nDone: {successful}/{len(results)} successful")
    if "csv" in output_formats:
        path = export_catalog_results(results, timestamp)
        console.print(f"[green]CSV:[/green] {path}")
    _print_catalog_report(results)


def _print_catalog_report(results: list) -> None:
    total = len(results)
    ok = sum(1 for r in results if r.adapter_result.success)
    fallback_used = sum(1 for r in results if r.fallback_used)
    table = Table(title="Market Catalog Report", show_lines=True)
    table.add_column("Indicator")
    table.add_column("Status")
    table.add_column("Provider used")
    table.add_column("Fallback?")
    table.add_column("Records")
    for r in results:
        status_str = "[green]OK[/green]" if r.adapter_result.success else "[red]FAIL[/red]"
        table.add_row(
            r.catalog_id,
            status_str,
            r.provider_used,
            "Y" if r.fallback_used else "N",
            str(len(r.adapter_result.records)),
        )
    console.print(table)
    console.print(f"Total: {ok}/{total} OK | Fallbacks used: {fallback_used}")


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
            "market:currency",
            "market:bonds",
            "market:gaps",
            "market:stabilize",
            "market:catalog",
            "market:catalog:validate",
            "market:catalog:list",
            "market:catalog:coverage",
            "market:update",
            "market:intelligence:init-db",
            "market:intelligence:update",
            "market:intelligence:quality",
            "market:intelligence:snapshot",
            "market:intelligence:datasheet",
            "market:intelligence:catalog",
            "market:intelligence:catalog:validate",
        ],
        help="POC command to run",
    )
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=900,
        help="Local cache TTL in seconds (default: 900)",
    )
    parser.add_argument(
        "--priority",
        default=None,
        choices=["critical", "high", "medium", "low"],
        help="Filter catalog by priority (used with market:catalog:list and market:update)",
    )
    parser.add_argument(
        "--category",
        default=None,
        help="Filter catalog by category (used with market:catalog:list)",
    )
    args = parser.parse_args()

    output_formats = {fmt.strip().lower() for fmt in args.output.split(",")}
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

    console.print(f"[bold blue]Market Data POC[/bold blue] — region: [cyan]{args.providers}[/cyan]")

    # 1. Load providers catalog
    all_providers = load_providers_yaml()
    selected_providers = filter_providers(all_providers, args.providers)
    if args.command in _COMMAND_PROVIDER_IDS:
        command_ids = _COMMAND_PROVIDER_IDS[args.command]
        selected_providers = [p for p in selected_providers if p["id"] in command_ids]
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

    # Catalog commands that don't need adapters — ejecutar antes de cargar adapters cuando sea posible
    catalog_loader = CatalogLoader()

    if args.command == "market:catalog":
        cmd_catalog_show(catalog_loader)
        return

    if args.command == "market:catalog:validate":
        valid = cmd_catalog_validate(catalog_loader)
        sys.exit(0 if valid else 1)

    if args.command == "market:catalog:list":
        cmd_catalog_list(catalog_loader, args.priority, args.category)
        return

    # 3. Filter unavailable adapters (no API key)
    available: List[BaseAdapter] = []
    unavailable_count = 0
    for adapter in adapters:
        if adapter.is_available():
            available.append(adapter)
        else:
            reason = "requires optional API key" if adapter.requires_api_key else "availability check failed"
            console.print(f"[yellow]Skipping '{adapter.name}' - {reason}[/yellow]")
            unavailable_count += 1

    console.print(f"Running {len(available)} adapters ({unavailable_count} skipped)...\n")

    # Catalog commands that need adapters
    if args.command == "market:catalog:coverage":
        cmd_catalog_coverage(catalog_loader, available)
        return

    if args.command == "market:update":
        cmd_market_update(catalog_loader, available, timestamp, output_formats)
        return

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

    if args.command in {"market:coverage", "market:gaps"}:
        print_gap_table(coverage, timestamp)
        if args.command == "market:gaps":
            return

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
        print_gap_table(coverage, timestamp)

    if "catalog" in output_formats:
        from exporters.catalog_generator import generate_catalog
        catalog_paths = generate_catalog(coverage, timestamp)
        console.print(f"[green]Catalog:[/green] {catalog_paths['markdown']}")

    # 9. Print summary table
    print_summary_table(coverage)

    # ── Market Intelligence commands ──────────────────────────────────────────
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

    if args.command == "market:intelligence:init-db":
        from app.modules.market_intelligence.cli.commands import cmd_init_db
        cmd_init_db()
        return

    if args.command == "market:intelligence:update":
        from app.modules.market_intelligence.cli.commands import cmd_update
        cmd_update(category=getattr(args, "category", None), priority=getattr(args, "priority", None))
        return

    if args.command == "market:intelligence:quality":
        from app.modules.market_intelligence.cli.commands import cmd_quality
        cmd_quality()
        return

    if args.command == "market:intelligence:snapshot":
        from app.modules.market_intelligence.cli.commands import cmd_snapshot
        cmd_snapshot()
        return

    if args.command == "market:intelligence:datasheet":
        from app.modules.market_intelligence.cli.commands import cmd_datasheet
        cmd_datasheet()
        return

    if args.command == "market:intelligence:catalog":
        from app.modules.market_intelligence.cli.commands import cmd_catalog_show
        cmd_catalog_show()
        return

    if args.command == "market:intelligence:catalog:validate":
        from app.modules.market_intelligence.cli.commands import cmd_catalog_validate
        valid = cmd_catalog_validate()
        _sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
