"""CLI principal — AI Financial OS Backend.

Uso:
    python cli.py <command>

Comandos disponibles:
    mi:init-db              Crear tablas DuckDB de Market Intelligence
    mi:catalog-show         Mostrar catálogo de indicadores
    mi:catalog-validate     Validar catálogo
    mi:update               Ejecutar ingesta de datos de mercado
    mi:backfill-history     Backfill de precios EOD (catalog opc, --years=N; ej: mi:backfill-history indices --years=5)
    mi:quality              Mostrar salud de proveedores
    mi:snapshot             Generar snapshot de Market Intelligence
    mi:datasheet            Generar AI datasheet de Market Intelligence

    knowledge:recompute     Ejecutar pipeline completo de Financial Knowledge
    knowledge:signals       Mostrar señales financieras activas
    knowledge:regime        Mostrar régimen de mercado actual
    knowledge:datasheet     Mostrar AI datasheet de Financial Knowledge
    knowledge:personal-impact  Mostrar impactos personales
"""
from __future__ import annotations

import sys


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    # Market Intelligence commands
    if cmd == "mi:init-db":
        from app.modules.market_intelligence.cli.commands import cmd_init_db
        cmd_init_db()

    elif cmd == "mi:catalog-show":
        from app.modules.market_intelligence.cli.commands import cmd_catalog_show
        cmd_catalog_show()

    elif cmd == "mi:catalog-validate":
        from app.modules.market_intelligence.cli.commands import cmd_catalog_validate
        cmd_catalog_validate()

    elif cmd == "mi:update":
        from app.modules.market_intelligence.cli.commands import cmd_update
        category = sys.argv[2] if len(sys.argv) > 2 else None
        priority = sys.argv[3] if len(sys.argv) > 3 else None
        dry_run = "--dry-run" in sys.argv
        cmd_update(category=category, priority=priority, dry_run=dry_run)

    elif cmd == "mi:backfill-history":
        from app.modules.market_intelligence.cli.commands import cmd_backfill_history
        catalog = next((a for a in sys.argv[2:] if not a.startswith("--")), None)
        years_arg = next((a for a in sys.argv[2:] if a.startswith("--years=")), None)
        years = int(years_arg.split("=", 1)[1]) if years_arg else 1
        cmd_backfill_history(catalog=catalog, years=years)

    elif cmd == "mi:quality":
        from app.modules.market_intelligence.cli.commands import cmd_quality
        cmd_quality()

    elif cmd == "mi:snapshot":
        from app.modules.market_intelligence.cli.commands import cmd_snapshot
        cmd_snapshot()

    elif cmd == "mi:datasheet":
        from app.modules.market_intelligence.cli.commands import cmd_datasheet
        scope = sys.argv[2] if len(sys.argv) > 2 else "daily"
        cmd_datasheet(scope=scope)

    # Financial Knowledge commands
    elif cmd == "knowledge:recompute":
        from app.modules.financial_knowledge.cli.commands import cmd_recompute
        cmd_recompute()

    elif cmd == "knowledge:signals":
        from app.modules.financial_knowledge.cli.commands import cmd_signals
        cmd_signals()

    elif cmd == "knowledge:regime":
        from app.modules.financial_knowledge.cli.commands import cmd_regime
        cmd_regime()

    elif cmd == "knowledge:datasheet":
        from app.modules.financial_knowledge.cli.commands import cmd_datasheet
        cmd_datasheet()

    elif cmd == "knowledge:personal-impact":
        from app.modules.financial_knowledge.cli.commands import cmd_personal_impact
        cmd_personal_impact()

    else:
        print(f"Comando desconocido: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
