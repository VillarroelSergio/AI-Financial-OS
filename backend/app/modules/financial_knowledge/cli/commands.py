"""Comandos CLI para el Financial Knowledge Layer."""
from __future__ import annotations
from rich.console import Console
from rich.table import Table

console = Console()


def cmd_recompute() -> None:
    from app.modules.financial_knowledge import service
    console.print("[cyan]Ejecutando pipeline Financial Knowledge...[/cyan]")
    result = service.recompute()
    status = "[green]OK[/green]" if result.success else "[yellow]PARCIAL[/yellow]"
    console.print(f"{status} {result.message}")
    console.print(f"  Insights: {result.insights_computed}")
    console.print(f"  Señales:  {result.signals_computed}")
    console.print(f"  Régimen:  {'OK' if result.regime_computed else 'ERROR'}")
    console.print(f"  Impactos: {result.impacts_computed}")
    console.print(f"  Datasheet: {'OK' if result.datasheet_generated else 'ERROR'}")
    for err in result.errors:
        console.print(f"  [red]ERROR:[/red] {err}")


def cmd_signals() -> None:
    from app.modules.financial_knowledge import service
    signals = service.get_signals()
    if not signals:
        console.print("[yellow]No hay señales. Ejecuta knowledge:recompute primero.[/yellow]")
        return
    table = Table(title="Señales Financieras Activas", show_lines=True)
    table.add_column("Tipo", style="bold")
    table.add_column("Severidad")
    table.add_column("Dirección")
    table.add_column("Confianza")
    table.add_column("Descripción")
    colors = {"critical": "red", "high": "yellow", "medium": "cyan", "low": "dim"}
    for sig in signals:
        sev = getattr(sig, "severity", "low")
        c = colors.get(sev, "white")
        table.add_row(
            getattr(sig, "signal_type", ""),
            f"[{c}]{sev}[/{c}]",
            getattr(sig, "direction", ""),
            f"{getattr(sig, 'confidence_score', 0):.0%}",
            (getattr(sig, "description", "") or "")[:60],
        )
    console.print(table)


def cmd_regime() -> None:
    from app.modules.financial_knowledge import service
    regime = service.get_regime()
    if not regime:
        console.print("[yellow]No hay régimen. Ejecuta knowledge:recompute primero.[/yellow]")
        return
    console.print("\n[bold]Régimen de Mercado[/bold]")
    console.print(f"  Risk Level:  [bold]{regime.risk_level}[/bold]")
    console.print(f"  Inflación:   {regime.inflation_regime}")
    console.print(f"  Tipos:       {regime.rates_regime}")
    console.print(f"  Crecimiento: {regime.growth_regime}")
    console.print(f"  Tendencia:   {regime.market_trend}")
    console.print(f"  Confianza:   {regime.confidence_score:.0%}")
    console.print(f"  Explicación: {regime.explanation}")


def cmd_datasheet() -> None:
    from app.modules.financial_knowledge import service
    ds = service.get_ai_datasheet()
    if not ds:
        console.print("[yellow]No hay datasheet. Ejecuta knowledge:recompute primero.[/yellow]")
        return
    console.print(f"\n[bold]AI Datasheet[/bold] (quality: {ds.quality_score:.2f})")
    console.print(f"  Señales:  {len(ds.financial_signals)}")
    console.print(f"  Insights: {len(ds.macro_insights)}")
    console.print(f"  Impactos: {len(ds.personal_impacts)}")
    for w in (ds.warnings or []):
        console.print(f"  [yellow]WARN:[/yellow] {w}")


def cmd_personal_impact() -> None:
    from app.modules.financial_knowledge import service
    impacts = service.get_personal_impacts()
    if not impacts:
        console.print("[yellow]No hay impactos. Ejecuta knowledge:recompute primero.[/yellow]")
        return
    table = Table(title="Impactos Personales", show_lines=True)
    table.add_column("Tipo", style="bold")
    table.add_column("Dominio")
    table.add_column("Severidad")
    table.add_column("Título")
    colors = {"critical": "red", "high": "yellow", "medium": "cyan", "low": "dim"}
    for impact in impacts:
        sev = getattr(impact, "severity", "low")
        c = colors.get(sev, "white")
        table.add_row(
            getattr(impact, "impact_type", ""),
            getattr(impact, "user_domain", ""),
            f"[{c}]{sev}[/{c}]",
            getattr(impact, "title", ""),
        )
    console.print(table)
