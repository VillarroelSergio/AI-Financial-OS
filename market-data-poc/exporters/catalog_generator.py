import csv
import dataclasses
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from models.evaluation import CoverageReport

_OUTPUT_DIR = Path(__file__).parent.parent / "output" / "catalog"

_MODEL_DESCRIPTIONS = {
    "MarketQuote": "Cotizaciones de mercado: acciones, indices, forex, cripto o bonos.",
    "HistoricalPrice": "Series historicas OHLCV.",
    "MacroIndicator": "Indicadores macroeconomicos puntuales o historicos.",
    "EconomicEvent": "Eventos de calendario economico.",
    "NewsItem": "Noticias financieras agregadas por RSS.",
    "MarketNews": "Noticias de mercado normalizadas.",
    "CompanyProfile": "Perfil e identificadores de companias o instrumentos.",
    "CompanyMetric": "Metricas fundamentales de companias.",
    "Dividend": "Dividendos proximos o historicos.",
    "ETF": "Datos de ETF: composicion, TER, paises, sectores y dividendos.",
    "Fund": "Datos de fondos: categoria, ISIN y rentabilidad.",
    "Commodity": "Materias primas: energia, metales o agricultura.",
    "Currency": "Pares de divisas.",
    "YieldCurve": "Curvas de tipos por vencimiento.",
    "EconomicCalendar": "Calendario macro: inflacion, PIB, tipos, PMI, NFP.",
    "MacroSeries": "Series macro completas con observaciones.",
    "CorporateAction": "Acciones corporativas.",
}


def generate_catalog(report: CoverageReport, timestamp: str | None = None) -> dict[str, Path]:
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = timestamp or datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    entries = [_entry_from_evaluation(ev) for ev in sorted(report.evaluations, key=lambda e: e.provider)]

    summary = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_providers": report.total_providers,
        "successful": report.successful,
        "failed": report.failed,
        "unavailable": report.unavailable,
        "record_models": sorted({model for entry in entries for model in entry["record_models"]}),
        "capabilities": sorted({cap for entry in entries for cap in entry["capabilities"]}),
        "entries": entries,
        "gaps": _gaps(entries),
    }

    json_path = _OUTPUT_DIR / f"{ts}_data_catalog.json"
    md_path = _OUTPUT_DIR / f"{ts}_data_catalog.md"
    csv_path = _OUTPUT_DIR / f"{ts}_data_catalog.csv"

    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8")
    md_path.write_text(_render_markdown(summary), encoding="utf-8")
    _write_csv(csv_path, entries)
    return {"json": json_path, "markdown": md_path, "csv": csv_path}


def _entry_from_evaluation(ev) -> dict[str, Any]:
    result = ev.adapter_result
    metadata = result.metadata
    records = result.records or []
    model_fields: dict[str, list[str]] = {}
    sample_records: dict[str, dict] = {}
    for record in records:
        model = _record_model(record)
        model_fields.setdefault(model, _record_fields(record))
        if model not in sample_records:
            sample_records[model] = _record_sample(record)

    return {
        "provider": ev.provider,
        "status": "ok" if result.success else "failed",
        "recommendation": ev.recommendation,
        "score": ev.score_total,
        "quality": ev.data_quality,
        "reliability": ev.reliability,
        "latency_ms": round(result.latency_ms, 2),
        "region": metadata.region,
        "category": metadata.category,
        "method": metadata.method,
        "base_url": metadata.base_url,
        "license": metadata.license,
        "requires_api_key": metadata.requires_api_key,
        "frequency": metadata.declared_update_frequency,
        "historical_depth_years": metadata.declared_historical_depth_years,
        "capabilities": list(metadata.capabilities or (metadata.category,)),
        "record_count": len(records),
        "record_models": sorted(model_fields),
        "model_fields": model_fields,
        "sample_records": sample_records,
        "information": [_MODEL_DESCRIPTIONS.get(model, model) for model in sorted(model_fields)],
        "error": result.error,
        "notes": metadata.notes,
    }


def _record_model(record) -> str:
    if dataclasses.is_dataclass(record) and not isinstance(record, type):
        return record.__class__.__name__
    if isinstance(record, dict):
        return record.get("model", "dict")
    return record.__class__.__name__


def _record_fields(record) -> list[str]:
    if dataclasses.is_dataclass(record) and not isinstance(record, type):
        return [field.name for field in dataclasses.fields(record)]
    if isinstance(record, dict):
        return sorted(record)
    return []


def _record_sample(record) -> dict:
    if dataclasses.is_dataclass(record) and not isinstance(record, type):
        data = dataclasses.asdict(record)
    elif isinstance(record, dict):
        data = dict(record)
    else:
        data = {"value": str(record)}
    return {key: _json_default(value) for key, value in list(data.items())[:12]}


def _gaps(entries: list[dict]) -> list[str]:
    expected = {
        "stocks", "etf", "funds", "macro", "bonds", "commodities", "currency",
        "crypto", "news", "dividends", "earnings", "economic_calendar",
        "historical", "intraday", "realtime",
    }
    covered = {cap for entry in entries if entry["status"] == "ok" for cap in entry["capabilities"]}
    gaps = sorted(expected - covered)
    failed = [entry["provider"] for entry in entries if entry["status"] != "ok"]
    return [f"Capability without successful provider: {gap}" for gap in gaps] + [
        f"Provider failed or returned no data: {provider}" for provider in failed
    ]


def _render_markdown(summary: dict) -> str:
    lines = [
        "# Market Data Catalog",
        "",
        f"**Generated:** {summary['generated_at']}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total providers | {summary['total_providers']} |",
        f"| Successful | {summary['successful']} |",
        f"| Failed | {summary['failed']} |",
        f"| Unavailable | {summary['unavailable']} |",
        f"| Record models | {', '.join(summary['record_models']) or 'None'} |",
        f"| Capabilities | {', '.join(summary['capabilities']) or 'None'} |",
        "",
        "## Provider Catalog",
        "",
        "| Provider | Status | Region | Category | Models | Records | Score | Recommendation |",
        "|----------|--------|--------|----------|--------|---------|-------|----------------|",
    ]
    for entry in summary["entries"]:
        lines.append(
            f"| {entry['provider']} | {entry['status']} | {entry['region']} | "
            f"{entry['category']} | {', '.join(entry['record_models']) or '-'} | "
            f"{entry['record_count']} | {entry['score']:.1f} | {entry['recommendation']} |"
        )

    lines.extend(["", "## Information By Provider", ""])
    for entry in summary["entries"]:
        lines.extend([
            f"### {entry['provider']}",
            "",
            f"- Status: {entry['status']}",
            f"- Region/category: {entry['region']} / {entry['category']}",
            f"- Capabilities: {', '.join(entry['capabilities']) or '-'}",
            f"- Models: {', '.join(entry['record_models']) or '-'}",
            f"- Fields: {_format_fields(entry['model_fields'])}",
            f"- Information: {'; '.join(entry['information']) or '-'}",
            f"- Records collected: {entry['record_count']}",
            f"- Frequency/history: {entry['frequency']} / {entry['historical_depth_years']} years",
            f"- Error: {entry['error'] or '-'}",
            "",
        ])

    lines.extend(["## Gaps", ""])
    if summary["gaps"]:
        lines.extend(f"- {gap}" for gap in summary["gaps"])
    else:
        lines.append("- No gaps detected.")
    lines.append("")
    return "\n".join(lines)


def _format_fields(model_fields: dict[str, list[str]]) -> str:
    if not model_fields:
        return "-"
    return "; ".join(f"{model}: {', '.join(fields)}" for model, fields in model_fields.items())


def _write_csv(path: Path, entries: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "provider", "status", "region", "category", "capabilities",
                "record_models", "record_count", "score", "recommendation",
                "latency_ms", "frequency", "historical_depth_years", "error",
            ],
        )
        writer.writeheader()
        for entry in entries:
            writer.writerow({
                "provider": entry["provider"],
                "status": entry["status"],
                "region": entry["region"],
                "category": entry["category"],
                "capabilities": ", ".join(entry["capabilities"]),
                "record_models": ", ".join(entry["record_models"]),
                "record_count": entry["record_count"],
                "score": entry["score"],
                "recommendation": entry["recommendation"],
                "latency_ms": entry["latency_ms"],
                "frequency": entry["frequency"],
                "historical_depth_years": entry["historical_depth_years"],
                "error": entry["error"] or "",
            })


def _json_default(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value
