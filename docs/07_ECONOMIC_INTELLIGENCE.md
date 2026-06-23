# 07 — Economic Intelligence

## Objetivo

Añadir una capa de datos económicos reales y actualizados centrados en España, Eurozona y Estados Unidos para contextualizar las finanzas personales, inversiones y objetivos.

## Principio de producto

La sección económica no debe convertirse en un portal macroeconómico genérico. Todo dato debe responder a:

> ¿Cómo puede afectar esto al dinero, gastos, ahorro, inversiones u objetivos del usuario?

## Regiones

- España.
- Eurozona.
- Estados Unidos.

## Indicadores V1

### España

- Inflación.
- Inflación subyacente.
- Tasa de paro.
- PIB.
- Euríbor.
- Bono español 10 años.
- IBEX 35.

### Eurozona

- Inflación.
- Inflación subyacente.
- Tasa de paro.
- PIB.
- Tipo BCE.
- Bund alemán 10 años.
- Euro Stoxx 50.
- STOXX Europe 600.

### Estados Unidos

- CPI.
- Core CPI.
- Unemployment Rate.
- GDP.
- Fed Funds Rate.
- Treasury 10Y.
- S&P 500.
- Nasdaq 100.
- Dow Jones.

### Divisas

- EUR/USD.

## Excluido V1

- Materias primas.
- Calendario macro completo.
- Forecasts de analistas.
- Noticias.
- Sentiment analysis.

## Fuentes candidatas

La implementación debe usar providers intercambiables. Las fuentes exactas pueden cambiar sin afectar al dominio.

Candidatas:

- INE para España.
- Banco de España para datos financieros españoles.
- Eurostat para Eurozona.
- BCE para tipos, divisas y datos monetarios.
- FRED para Estados Unidos.
- APIs de mercado para índices y divisas.

## Arquitectura

```txt
economic_data/
  providers/
    ine_provider.py
    eurostat_provider.py
    ecb_provider.py
    fred_provider.py
    market_provider.py
  service.py
  repository.py
  routes.py
  schemas.py
```

## Frecuencia

```txt
Índices              Diario
Divisas              Diario
Bonos                Diario
Euríbor              Diario
Inflación            Mensual
Paro                 Mensual / trimestral
PIB                  Trimestral
Tipos BCE/FED        Según reunión
```

## Caché

Todos los datos descargados deben almacenarse localmente.

Campos obligatorios:

- Fuente.
- Fecha de observación.
- Fecha de descarga.
- Fecha de publicación si existe.
- Unidad.

## UX

La pantalla Economy debe ser un snapshot, no una tabla compleja.

Estructura:

```txt
Economy
 ├─ Snapshot global
 ├─ España
 ├─ Eurozona
 ├─ EEUU
 ├─ Tipos
 ├─ Inflación
 └─ Impacto en tus finanzas
```

## Card de indicador

```txt
Inflación España
3,2%
+0,4 pp vs dato anterior
Último dato: mayo 2026
Fuente: INE
```

## Vista de impacto personal

La sección más diferencial:

```txt
Impacto en tus finanzas
 ├─ Inflación vs gasto personal
 ├─ Tipos vs cuentas remuneradas
 ├─ Mercado vs inversiones
 ├─ Inflación vs objetivos
 └─ Bonos/tipos vs perfil conservador
```

## Tools IA futuras

```txt
get_macro_snapshot(region)
get_indicator_latest(code, region)
get_indicator_history(code, region, start_date, end_date)
compare_macro_regions(indicator)
explain_macro_personal_impact(indicator, user_context)
```

## Ejemplos de insights

- La inflación está por encima del crecimiento de tu ahorro mensual.
- Los tipos elevados favorecen la rentabilidad de tu liquidez.
- Tu cartera cae en línea con los principales índices.
- Tu objetivo de ahorro debería revisarse si quieres mantener poder adquisitivo real.

## Reglas de diseño

- Máximo 4 indicadores por región en overview.
- No mostrar calendarios macro completos en V1.
- No mezclar noticias con datos.
- No usar colores alarmistas.
- Mostrar siempre fecha y fuente.
