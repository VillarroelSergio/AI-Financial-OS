"""Comandos CLI para el Market Intelligence Layer."""
from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()
OUTPUT_DIR = Path("output/market-intelligence")


def cmd_init_db() -> None:
    from app.core.duckdb import get_duckdb
    from app.modules.market_intelligence.storage.migrations import run_migrations
    conn = get_duckdb()
    run_migrations(conn)
    console.print("[green]OK[/green] DuckDB tables created")


def cmd_catalog_show() -> None:
    from app.modules.market_intelligence.catalog.loader import CatalogLoader
    loader = CatalogLoader()
    items = loader.load_all()
    table = Table(title="Market Data Catalog", show_lines=True)
    table.add_column("ID", style="bold")
    table.add_column("Name")
    table.add_column("Priority")
    table.add_column("Freq")
    table.add_column("AI")
    table.add_column("Primary")
    for item in items:
        color = {"critical": "red", "high": "yellow", "medium": "cyan", "low": "dim"}.get(item.priority, "white")
        table.add_row(
            item.id, item.name,
            f"[{color}]{item.priority}[/{color}]",
            item.frequency,
            "Y" if item.ai else "",
            item.provider_primary,
        )
    console.print(table)
    console.print(f"\nTotal: {len(items)} | Critical: {sum(1 for i in items if i.priority=='critical')} | AI: {sum(1 for i in items if i.ai)}")


def cmd_catalog_validate() -> bool:
    from app.modules.market_intelligence.catalog.loader import CatalogLoader
    loader = CatalogLoader()
    errors = loader.validate()
    if not errors:
        console.print(f"[green]OK[/green] Catalog valid — {len(loader.load_all())} indicators loaded")
        return True
    console.print(f"[red]ERROR[/red] {len(errors)} validation error(s):")
    for e in errors:
        console.print(f"  [red]• {e}[/red]")
    return False


def cmd_update(category: str | None = None, priority: str | None = None, dry_run: bool = False) -> None:
    from app.modules.market_intelligence.ingestion.runner import run_ingestion
    label = f"category={category or 'all'} priority={priority or 'all'}"
    console.print(f"[bold blue]Market Intelligence Update[/bold blue] — {label}")
    if dry_run:
        console.print("[yellow]DRY RUN — no data will be persisted[/yellow]")
    summary = run_ingestion(category=category, priority=priority, dry_run=dry_run)
    console.print(f"\n[bold]Done[/bold] run={summary.run_id}")
    console.print(f"  Total: {summary.total} | [green]OK: {summary.success}[/green] | [red]Failed: {summary.failed}[/red] | Fallbacks: {summary.fallbacks_used}")
    duration = (summary.finished_at - summary.started_at).total_seconds()
    console.print(f"  Duration: {duration:.1f}s")


def cmd_quality() -> None:
    from app.core.duckdb import get_duckdb
    conn = get_duckdb()
    rows = conn.execute(
        "SELECT provider_id, status, COUNT(*) as count FROM mi_provider_health_logs GROUP BY provider_id, status ORDER BY provider_id"
    ).fetchall()
    table = Table(title="Provider Health Summary", show_lines=True)
    table.add_column("Provider")
    table.add_column("Status")
    table.add_column("Count", justify="right")
    for row in rows:
        status_color = "green" if row[1] == "success" else "red"
        table.add_row(row[0], f"[{status_color}]{row[1]}[/{status_color}]", str(row[2]))
    console.print(table)


def cmd_snapshot() -> None:
    from app.modules.market_intelligence.storage.snapshot import generate_snapshot
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = generate_snapshot()
    path = OUTPUT_DIR / "market_intelligence_snapshot.json"
    path.write_text(json.dumps(snapshot, indent=2, default=str), encoding="utf-8")
    console.print(f"[green]Snapshot written:[/green] {path}")


def cmd_datasheet(scope: str = "daily") -> None:
    from app.modules.market_intelligence.ai.datasheet import generate_ai_datasheet
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    datasheet = generate_ai_datasheet(scope=scope)
    path = OUTPUT_DIR / f"ai_datasheet_{scope}.json"
    path.write_text(json.dumps(datasheet.model_dump(), indent=2, default=str), encoding="utf-8")
    console.print(f"[green]AI Datasheet written:[/green] {path}")
    console.print(f"  Quality score: {datasheet.quality_score:.3f} | Warnings: {len(datasheet.warnings)}")
