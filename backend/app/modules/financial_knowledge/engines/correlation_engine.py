"""Correlation Engine — relaciona señales macro con activos y dominios personales."""
from __future__ import annotations
import logging
import uuid
from datetime import datetime, timezone

from app.modules.financial_knowledge.models import CorrelationInsight, FinancialSignal

logger = logging.getLogger("financial_knowledge.correlation_engine")

# Mapa de señal → correlaciones (asset_type, user_domain, relationship_type, description)
_SIGNAL_CORRELATIONS: dict[str, list[tuple[str, str, str, str]]] = {
    "inflation_above_target": [
        ("cash", "cash", "erodes_value", "La inflación erosiona el poder adquisitivo del efectivo"),
        ("savings", "savings", "erodes_value", "Las cuentas de ahorro pierden valor real con inflación alta"),
        ("bonds_fixed", "portfolio", "reduces_real_return", "Los bonos de cupón fijo pierden valor real"),
    ],
    "rates_high": [
        ("mortgage_variable", "mortgage", "increases_cost", "Los tipos altos encarecen hipotecas variables"),
        ("bonds", "portfolio", "price_pressure", "Los bonos existentes bajan de precio cuando suben tipos"),
        ("real_estate", "real_estate", "reduces_demand", "Tipos altos frenan la demanda inmobiliaria"),
        ("savings_account", "savings", "increases_return", "Las cuentas remuneradas mejoran con tipos altos"),
    ],
    "rates_high#euribor_rising": [
        ("mortgage_variable_euribor", "mortgage", "increases_cost", "El Euríbor más alto encarece hipotecas referenciadas"),
    ],
    "equity_market_drawdown": [
        ("equities", "portfolio", "direct_loss", "Caída directa en el valor de la cartera de renta variable"),
        ("etf_equity", "portfolio", "direct_loss", "Los ETFs de renta variable acusan la caída del mercado"),
    ],
    "usd_strength": [
        ("usd_assets", "portfolio", "currency_gain_for_usd_holders", "Activos en USD valen más en EUR si el dólar sube"),
    ],
    "eur_weakness": [
        ("international_equities", "portfolio", "fx_impact", "Activos internacionales en USD suben al debilitarse el EUR"),
        ("imports", "expenses", "increases_cost", "Las importaciones se encarecen con el euro débil"),
    ],
    "oil_spike": [
        ("transport", "expenses", "increases_cost", "El petróleo más caro encarece el transporte y la gasolina"),
        ("energy_stocks", "portfolio", "sector_benefit", "Las empresas energéticas se benefician de precios altos del petróleo"),
    ],
    "electricity_price_spike": [
        ("energy_bill", "expenses", "increases_cost", "La factura eléctrica sube directamente"),
        ("industrial_stocks", "portfolio", "cost_pressure", "Empresas industriales intensivas en energía acusan el coste"),
    ],
    "yield_curve_inverted": [
        ("bonds_long_term", "portfolio", "risk_signal", "Curva invertida señala posible recesión — bonos largos en riesgo"),
        ("equities", "portfolio", "recession_risk", "Curva invertida históricamente precede caídas en bolsa"),
    ],
    "employment_weakening": [
        ("equities", "portfolio", "demand_concern", "Menor empleo reduce consumo y presiona beneficios empresariales"),
        ("income", "income", "risk_signal", "Deterioro del empleo aumenta el riesgo de pérdida de ingresos"),
    ],
}


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


def compute_correlations(signals: list[FinancialSignal]) -> list[CorrelationInsight]:
    """Genera correlaciones entre señales activas y activos/dominios del usuario."""
    insights: list[CorrelationInsight] = []
    now = _now()

    for signal in signals:
        correlations = _SIGNAL_CORRELATIONS.get(signal.signal_type, [])
        for asset_type, user_domain, rel_type, description in correlations:
            insights.append(CorrelationInsight(
                id=_uid(),
                signal_id=signal.id,
                signal_type=signal.signal_type,
                asset_type=asset_type,
                user_domain=user_domain,
                relationship_type=rel_type,
                description=description,
                confidence_score=signal.confidence_score * 0.9,
                computed_at=now,
            ))

    logger.info("CorrelationEngine: %d correlaciones generadas", len(insights))
    return insights
