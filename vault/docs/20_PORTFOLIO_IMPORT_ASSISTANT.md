# 20 — Portfolio Import Assistant

## Objetivo

Permitir al usuario crear la cartera inicial desde capturas de pantalla de su broker o mediante entrada manual rápida, sin necesidad de un CSV exportado.

## Principio clave

La importación es **asistida, no automática**. Los datos extraídos pueden contener errores. Ningún holding se crea sin revisión y confirmación explícita del usuario.

## Flujo

```
Inversiones → "Importar cartera"
→ Elegir método: "Desde captura" o "Entrada rápida"
→ Pegar texto copiado del broker
→ Extracción local (sin red externa)
→ Validación de instrumento + precio + FX
→ Tabla editable de revisión
→ Confirmar importación
→ Holdings creados
```

## Parser de texto

El texto se extrae localmente mediante expresiones regulares. No se envía ninguna imagen ni texto a servicios externos.

Formato compatible (bloques separados por línea en blanco):

```
Apple
x 0,564555
140,15 €
+38,76 %

Microsoft
x 1,234
280,50 €
-5,23 %
```

Campos detectados por bloque:
- **Nombre del activo**: primera línea del bloque
- **Cantidad**: línea con prefijo `x` o número puro
- **Valor actual**: número + símbolo de divisa (€, $, £, A$)
- **Rentabilidad**: número seguido de `%`, con signo opcional

## Coste estimado

Cuando la captura incluye valor actual y rentabilidad porcentual:

```
coste_estimado = valor_actual / (1 + rentabilidad / 100)
```

Este dato se marca siempre como `~estimado`. No debe usarse como precio medio fiscal exacto.

## Estados de importación

| Estado | Significado |
|---|---|
| `READY` | Instrumento resuelto + precio disponible → puede importarse |
| `REQUIRES_CONFIRMATION` | Ticker ambiguo (ej. SpaceX/SPCX) — el usuario debe confirmar |
| `NO_PRICE` | Instrumento encontrado pero sin precio de mercado → importar como manual |
| `MANUAL` | Usuario lo marcó explícitamente como manual (sin actualización automática) |
| `REVIEW` | Datos incompletos o instrumento no encontrado |
| `DISCARDED` | El usuario descartó la fila |
| `IMPORTED` | Importado correctamente |

## Validación de instrumentos

Reutiliza `resolve_asset()` de `asset_resolution.py`. Casos cubiertos:
- BBVA → BBVA.MC (BME/EUR), no el ADR de NYSE
- ASML → ASML.AS (Euronext Amsterdam/EUR), no el ADR de NASDAQ
- SpaceX → SPCX requiere confirmación (empresa privada; SPCX es ETF no relacionado)
- DroneShield → DRO.AX (ASX/AUD)

## Cobertura de precios y FX

Reutiliza `audit_asset()` de `price_coverage_audit.py`. Integra:
- Precio actual del instrumento
- Conversión FX a EUR (EURUSD, EURAUD, EURGBP, EURCHF)
- Estado de cobertura (OK, FX_PENDING, UNAVAILABLE)

## Activos manuales

Los activos sin precio de mercado, privados, o marcados manualmente por el usuario se guardan con `price_source = "manual"`. No se intentará actualización automática.

## Gestión de duplicados

Antes de confirmar, el usuario puede detectar posibles duplicados por ticker (normalizado). La app no duplica automáticamente ni elimina posiciones existentes.

Normalización de tickers duplicados: `BRK-B`, `BRK.B`, `BRK/B` → todos se tratan como `BRK-B`.

## Trazabilidad

Cada holding importado registra:
- `price_source`: `"auto"` o `"manual"`
- Si el coste fue estimado, queda en los metadatos de la posición

## Seguridad

- Las imágenes nunca salen del equipo (el flujo actual usa pegado de texto, no OCR remoto)
- No se envía texto financiero a servicios cloud no definidos
- No hay scraping ni sincronización bancaria
- No se crean holdings sin confirmación explícita

## API

```
POST /api/investments/import/parse-text
  Body: { text: string }
  Returns: RawPosition[]

POST /api/investments/import/validate
  Body: { positions: RawPosition[] }
  Returns: ValidatedPosition[]

POST /api/investments/import/check-duplicates
  Body: { ticker: string, account_id?: string }
  Returns: DuplicateCheckOut

POST /api/investments/import/confirm
  Body: { positions: ConfirmPositionIn[] }
  Returns: ConfirmBatchOut
```

## Archivos clave

| Archivo | Propósito |
|---|---|
| `backend/app/modules/investments/portfolio_import_service.py` | Parser, validador, estimador de coste, creación de holdings |
| `backend/app/modules/investments/portfolio_import_routes.py` | Endpoints FastAPI |
| `apps/desktop/src/features/investments/import/PortfolioImportPage.tsx` | Página principal |
| `apps/desktop/src/features/investments/import/ImportReviewTable.tsx` | Tabla editable de revisión |
| `apps/desktop/src/lib/types/portfolio-import.ts` | Tipos TypeScript |
| `apps/desktop/src/lib/api/portfolio-import.ts` | Cliente API |

## Fase 10.5 - Alcance de capturas reales

La UI acepta varias capturas (`png`, `jpg`, `webp`) para representar el caso de uso real de importacion desde broker. En la build actual no hay OCR local activado todavia: las imagenes no se guardan, no se procesan en cloud y no crean holdings. La pantalla comunica este alcance de forma explicita y ofrece texto pegado como fallback revisable.

Camino futuro:

- OCR local.
- Extraccion local de tablas/posiciones.
- Marcado de campos capturados vs estimados vs confirmados.
- Comparacion visual contra la captura antes de confirmar.
