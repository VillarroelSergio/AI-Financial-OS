"""ECO-4 (task 2, opción B): umbrales de las comparativas de impacto personal.

Fuera del código, patrón Insights Engine. Ajustar una comparativa = cambiar aquí sin tocar
la lógica de `impact.py`. Valores en las unidades del propio indicador (%, meses, bps,
USD/barril, ratio EUR/USD). Son umbrales de comparación (no aritmética de dinero) → float.
"""

# Liquidez: meses de gasto cubiertos por el efectivo.
LIQUIDITY_MIN_MONTHS = 3.0
LIQUIDITY_MIN_MONTHS_LOW_CONFIDENCE = 6.0
CONSUMER_CONFIDENCE_LOW = 90.0  # confianza por debajo → exige más colchón

# Inflación / poder adquisitivo (IPC general, %).
INFLATION_BCE_TARGET = 2.0
INFLATION_HIGH = 3.0

# Euríbor 12M (%): por encima encarece la hipoteca variable.
EURIBOR_COMFORT_MAX = 3.0

# EUR/USD: por encima, euro fuerte (compras en USD más baratas).
EURUSD_STRONG_EURO = 1.10

# Petróleo Brent (USD/barril) y su variación interanual (%) como proxy energético.
BRENT_FAVORABLE = 80.0
BRENT_HIGH = 90.0
ENERGY_YOY_UP = 10.0
ENERGY_YOY_DOWN = -10.0

# Prima de riesgo España (bps): diferencial bono 10Y ES vs bund.
RISK_PREMIUM_LOW = 100.0
RISK_PREMIUM_HIGH = 200.0

# Mínimo de cuantificación €/mes para añadir el texto de impacto (evita "0 €/mes").
MIN_EUR_PER_MONTH_TO_SHOW = 1.0
