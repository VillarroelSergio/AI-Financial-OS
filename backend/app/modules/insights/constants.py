from decimal import Decimal

SPENDING_ANOMALY_MULTIPLIER = Decimal("1.25")
SPENDING_ANOMALY_MIN_ABSOLUTE_EUR = Decimal("30")
SPENDING_ANOMALY_MIN_CURRENT_EUR = Decimal("50")
BASELINE_MONTHS = 3
MIN_BASELINE_MONTHS = 2
EXPENSE_DELTA_PERCENTAGE_THRESHOLD = Decimal("15")
SAVINGS_DELTA_ABSOLUTE_THRESHOLD_EUR = Decimal("50")
NET_WORTH_CHANGE_PERCENTAGE_THRESHOLD = Decimal("3")
NET_WORTH_CHANGE_ABSOLUTE_THRESHOLD_EUR = Decimal("500")
HIGH_CONCENTRATION_THRESHOLD = Decimal("40")
BROKER_CASH_THRESHOLD = Decimal("50")
GOAL_LAG_THRESHOLD_PERCENTAGE_POINTS = Decimal("10")
MARKET_DAILY_CHANGE_THRESHOLD = Decimal("1.5")
# INS-5 (Lote 1: planificación)
UPCOMING_CASHFLOW_DAYS = 15                       # ventana de vencimientos recurrentes a vigilar
RECURRING_CREEP_LOOKBACK_DAYS = 90               # "vs hace 3 meses" = altas de los últimos 90 días
RECURRING_CREEP_PCT_THRESHOLD = Decimal("15")    # % de crecimiento del gasto recurrente comprometido
# INS-6 (Lote 2: tendencias y patrimonio)
SAVINGS_RATE_TREND_MONTHS = 6                     # ventana de meses previos que se examinan
SAVINGS_RATE_TREND_MIN_MONTHS = 3                # mínimo de meses con ingresos para dar señal
SAVINGS_RATE_TREND_DELTA_PP = Decimal("5")       # cambio sostenido mínimo (puntos porcentuales)
CATEGORY_TREND_MONTHS = 3                         # meses consecutivos crecientes que definen tendencia
CATEGORY_TREND_MIN_EUR = Decimal("50")           # gasto mínimo del último mes para que importe
CATEGORY_TREND_GROWTH_PCT = Decimal("25")        # crecimiento acumulado mínimo primer→último mes
EMERGENCY_FUND_EXPENSE_LOOKBACK = 3              # meses para la media de gasto mensual
EMERGENCY_FUND_MONTHS_THRESHOLD = Decimal("3")   # colchón recomendado (meses de gasto)
DEFAULT_LIMIT = 10
MAX_INSIGHTS = 50

SEVERITY_SCORES = {
    "positive": 40,
    "info": 50,
    "warning": 75,
    "critical": 95,
}
CONFIDENCE_SCORES = {
    "complete": 90,
    "partial": 65,
    "insufficient": 30,
    "empty": 20,
    "error": 10,
}
FRESHNESS_SCORES = {
    "current": 100,
    "previous": 80,
    "older": 50,
}
