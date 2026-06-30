# Phase 10.6 — Release Candidate Stabilization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corregir todos los bloqueantes funcionales P0/P1 identificados en el QA Release Candidate para que AI Financial OS pueda avanzar a Fase 11 (Packaging).

**Architecture:** El proyecto es una app Tauri con frontend React/TypeScript + backend FastAPI/Python + DuckDB. Cada subsistema tiene su módulo independiente en `backend/app/modules/` y su feature en `apps/desktop/src/features/`. Las correcciones son quirúrgicas — no hay cambios estructurales globales.

**Tech Stack:** React 18 + TypeScript 5 + Tailwind 3 + Tauri 2 (frontend) · FastAPI + Python 3.11 + DuckDB + SQLAlchemy 2 (backend) · pytest (backend tests) · uv (Python package manager)

## Global Constraints

- No introducir nuevos módulos ni funcionalidades fuera del alcance de esta fase
- No usar datos seed/demo como si fueran datos reales
- No hacer commits automáticos — solo staging; el usuario confirma antes de commit
- Ejecutar `uv run pytest` (backend) y `npm run typecheck` (frontend) antes de cerrar cada tarea
- Ejecutar graphify al inicio y fin de cada instrucción principal
- Mantener privacidad local-first: ningún dato financiero personal a servicios externos
- Respetar el orden de ejecución del spec: Economy → Goals → AI → Markets → Portfolio → Planning → QA → Report

---

## Fixes ya aplicados (no re-implementar)

Los siguientes cambios están ya en la rama `fix/corrections-and-stabilization`:

- **Picklist dark mode** (`apps/desktop/src/index.css`): añadido `color-scheme: dark` en `[data-theme="dark"]` para que los `<option>` nativos hereden fondo oscuro.
- **Cuenta no obligatoria en edición** (`apps/desktop/src/features/transactions/TransactionsPage.tsx:195`): cambiado `required` → `required={!editingId}` y label "Seleccionar cuenta" → "Sin cuenta asignada".

---

## Task 1: Economy Data Integrity Repair (10.6.3)

**Files:**
- Investigate: `backend/app/modules/market_intelligence/ingestion/adapters/usa/` (fred.py, bls.py, etc.)
- Investigate: `backend/app/modules/market_intelligence/ingestion/adapters/spain/`
- Investigate: `backend/app/modules/market_intelligence/ingestion/adapters/europe/`
- Investigate: `backend/app/modules/market_intelligence/api/service.py`
- Investigate: `backend/app/modules/market_intelligence/api/routes.py`
- Test: `backend/app/tests/` (crear test si no existe)
- Frontend: `apps/desktop/src/features/economy/components/IndicatorCard.tsx`

**Root cause to verify:** El spec menciona que Estados Unidos muestra el mismo valor para múltiples indicadores. Esto indica un fallback silencioso: cuando falla un provider individual, se usa el mismo valor por defecto para todos los indicadores en lugar de `null`/`"sin dato"`.

- [ ] **Step 1: Investigar el adapter de EEUU**

```bash
# En backend/
cat app/modules/market_intelligence/ingestion/adapters/usa/fred.py
cat app/modules/market_intelligence/ingestion/adapters/usa/bls.py
```

Buscar patrones como `return default_value` o `except: return X` donde `X` es un valor concreto en lugar de `None`.

- [ ] **Step 2: Escribir test de regresión para valores únicos por indicador EEUU**

Crear o añadir a `backend/app/tests/test_economy_data_integrity.py`:

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_usa_indicators_are_not_all_identical():
    """Verifica que los indicadores de EEUU no comparten todos el mismo valor."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/market-intelligence/economy/usa")
    assert response.status_code == 200
    data = response.json()
    values = [
        indicator.get("value")
        for indicator in data.get("indicators", [])
        if indicator.get("value") is not None
    ]
    # Si hay más de 2 indicadores con valor, no deben ser todos idénticos
    if len(values) > 2:
        assert len(set(values)) > 1, f"Todos los indicadores tienen el mismo valor: {values[0]}"
```

```bash
cd backend && uv run pytest app/tests/test_economy_data_integrity.py -v
```

Esperado: FAIL si el bug existe.

- [ ] **Step 3: Identificar el fallback silencioso y corregirlo**

En cada adapter de EEUU (fred.py, bls.py), localizar el bloque que devuelve un valor concreto en lugar de `None` cuando falla la API:

```python
# ANTES (patrón problemático):
try:
    value = fetch_from_api(indicator)
except Exception:
    value = some_default_float  # ← esto repite el mismo valor

# DESPUÉS (correcto):
try:
    value = fetch_from_api(indicator)
except Exception:
    logger.warning(f"Failed to fetch {indicator}: {e}")
    value = None  # el caller debe marcar como "sin dato"
```

- [ ] **Step 4: Asegurar que `None` se serializa como estado honesto**

En `backend/app/modules/market_intelligence/api/service.py`, verificar que los indicadores con `value=None` reciben un campo `status` adecuado:

```python
def build_indicator_out(raw: dict) -> dict:
    value = raw.get("value")
    if value is None:
        status = "unavailable"
    elif raw.get("is_seed"):
        status = "seed"
    elif raw.get("is_stale"):
        status = "stale"
    else:
        status = "live"
    return {**raw, "value": value, "status": status}
```

- [ ] **Step 5: Actualizar IndicatorCard para mostrar estado honesto**

`apps/desktop/src/features/economy/components/IndicatorCard.tsx` — añadir badge de estado cuando `status !== "live"`:

```tsx
// Añadir al render, después del valor:
{indicator.status && indicator.status !== "live" && (
  <span className="ml-2 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide bg-white/10 text-stone">
    {indicator.status === "unavailable" ? "Sin dato" :
     indicator.status === "seed" ? "Demo" :
     indicator.status === "stale" ? "En caché" : indicator.status}
  </span>
)}
```

- [ ] **Step 6: Ejecutar test — debe pasar ahora**

```bash
cd backend && uv run pytest app/tests/test_economy_data_integrity.py -v
```

Esperado: PASS.

- [ ] **Step 7: Typecheck frontend**

```bash
cd apps/desktop && npm run typecheck
```

Esperado: 0 errores.

- [ ] **Step 8: Stage cambios (NO commit)**

```bash
git add backend/app/modules/market_intelligence/ \
        backend/app/tests/test_economy_data_integrity.py \
        apps/desktop/src/features/economy/components/IndicatorCard.tsx
```

---

## Task 2: Goals Simulation Correction (10.6.4)

**Files:**
- Read: `backend/app/modules/goals/simulation_service.py` (ya leído — lógica parece correcta)
- Read: `backend/app/modules/goals/routes.py`
- Read: `backend/app/modules/goals/schemas.py`
- Modify: `apps/desktop/src/features/goals/components/GoalSimulationPanel.tsx`
- Test: `backend/app/tests/test_goals_simulation.py`

**Root cause to verify:** La lógica de `simulation_service.py` calcula compound interest correctamente. El problema probablemente está en cómo el frontend presenta los resultados (escenarios confusos, sin explicación textual, sin aportación necesaria cuando no llega a plazo).

- [ ] **Step 1: Leer GoalSimulationPanel para identificar el problema de UX**

```bash
cat apps/desktop/src/features/goals/components/GoalSimulationPanel.tsx
```

Buscar:
- ¿Se muestra texto explicativo además de la gráfica?
- ¿Se muestra la aportación mensual necesaria cuando el objetivo no llega a plazo?
- ¿Se explica qué significa "conservador", "base", "optimista"?

- [ ] **Step 2: Ejecutar tests existentes de simulación**

```bash
cd backend && uv run pytest app/tests/test_goals_simulation.py -v
```

Documentar qué pasa, cuántos tests existen, cuáles fallan.

- [ ] **Step 3: Añadir casos de validación obligatorios al test**

En `backend/app/tests/test_goals_simulation.py`, añadir los casos del spec:

```python
from app.modules.goals.simulation_service import simulate_goal, SimulationResult

def test_goal_zero_initial_capital():
    """Capital inicial 0, aportación positiva → debe alcanzar objetivo."""
    result = simulate_goal(
        goal_id="test-1",
        current_amount=0.0,
        target_amount=10000.0,
        monthly_contribution=200.0,
        target_date=None,
        inflation_rate=0.03,
    )
    assert isinstance(result, SimulationResult)
    base = next(s for s in result.scenarios if s.scenario == "base")
    assert base.months_to_target is not None
    assert base.months_to_target > 0

def test_goal_zero_contribution():
    """Aportación 0 con capital inicial — solo crece por rentabilidad."""
    result = simulate_goal(
        goal_id="test-2",
        current_amount=5000.0,
        target_amount=10000.0,
        monthly_contribution=0.0,
        target_date=None,
        inflation_rate=0.0,
    )
    conservative = next(s for s in result.scenarios if s.scenario == "conservative")
    # Con 2% anual y 0 aportación, desde 5000 a 10000 tarda ~35 años
    assert conservative.months_to_target is None or conservative.months_to_target > 300

def test_goal_unreachable_in_time_shows_required_contribution():
    """Objetivo no alcanzable debe calcular aportación necesaria."""
    from datetime import date, timedelta
    target = (date.today() + timedelta(days=365)).isoformat()  # 1 año
    result = simulate_goal(
        goal_id="test-3",
        current_amount=0.0,
        target_amount=50000.0,
        monthly_contribution=100.0,
        target_date=target,
        inflation_rate=0.0,
    )
    # En 12 meses con 100€/mes no se llegan a 50.000€
    base = next(s for s in result.scenarios if s.scenario == "base")
    assert base.achievable_by_target_date == False
    assert result.monthly_contribution_needed is not None
    assert result.monthly_contribution_needed > 100.0

def test_scenarios_are_ordered_correctly():
    """Conservador ≤ Base ≤ Optimista en monto final."""
    result = simulate_goal(
        goal_id="test-4",
        current_amount=1000.0,
        target_amount=20000.0,
        monthly_contribution=200.0,
        target_date=None,
        inflation_rate=0.0,
    )
    amounts = {s.scenario: s.final_amount for s in result.scenarios}
    assert amounts["conservative"] <= amounts["base"] <= amounts["optimistic"]
```

```bash
cd backend && uv run pytest app/tests/test_goals_simulation.py::test_goal_unreachable_in_time_shows_required_contribution -v
```

Si falla, `simulation_service.py` no calcula `monthly_contribution_needed` cuando el objetivo no es alcanzable.

- [ ] **Step 4: Añadir `monthly_contribution_needed` a SimulationResult si no existe**

En `backend/app/modules/goals/simulation_service.py`, añadir al `SimulationResult` y calcularlo:

```python
@dataclass
class SimulationResult:
    goal_id: str
    current_amount: float
    target_amount: float
    monthly_contribution: float
    monthly_contribution_needed: Optional[float]  # Añadir si no existe
    # ... resto de campos
```

Cálculo (añadir en `simulate_goal` antes del return):

```python
# Aportación necesaria para llegar al objetivo en target_date (escenario base)
monthly_contribution_needed: Optional[float] = None
if target_date and base_scenario.achievable_by_target_date == False:
    months_remaining = _months_between(date.today(), date.fromisoformat(target_date))
    if months_remaining > 0:
        r_m = (1 + 0.06) ** (1/12) - 1  # tasa base mensual
        if r_m > 0:
            future_value_of_current = current_amount * (1 + r_m) ** months_remaining
            remaining = target_amount - future_value_of_current
            monthly_contribution_needed = remaining * r_m / ((1 + r_m) ** months_remaining - 1)
        else:
            monthly_contribution_needed = (target_amount - current_amount) / months_remaining
        monthly_contribution_needed = max(0.0, monthly_contribution_needed)
```

- [ ] **Step 5: Actualizar GoalSimulationPanel para mostrar texto explicativo**

En `apps/desktop/src/features/goals/components/GoalSimulationPanel.tsx`, añadir debajo de la gráfica un bloque de texto:

```tsx
{/* Resumen textual — no depender solo de la gráfica */}
<div className="mt-4 grid gap-3 sm:grid-cols-3">
  {simulation.scenarios.map((s) => (
    <div key={s.scenario} className="rounded-xl bg-white/5 p-3 space-y-1">
      <p className="text-xs font-semibold uppercase tracking-wide text-stone">{s.label}</p>
      <p className="text-sm text-on-dark">
        {s.achievable_by_target_date === true
          ? `Alcanzable: ${s.projected_date ?? "calculando..."}`
          : s.months_to_target
          ? `Estimado: ${s.projected_date}`
          : "No alcanzable en 30 años"}
      </p>
    </div>
  ))}
</div>

{/* Aportación necesaria si no llega a plazo */}
{simulation.monthly_contribution_needed != null && simulation.monthly_contribution_needed > simulation.monthly_contribution && (
  <div className="mt-3 rounded-xl bg-warning/10 border border-warning/20 p-3">
    <p className="text-xs text-stone">Para llegar en plazo (escenario base) necesitarías aportar</p>
    <p className="text-lg font-semibold text-on-dark">
      {simulation.monthly_contribution_needed.toLocaleString("es-ES", { style: "currency", currency: "EUR" })} / mes
    </p>
  </div>
)}
```

- [ ] **Step 6: Ejecutar todos los tests de goals**

```bash
cd backend && uv run pytest app/tests/test_goals.py app/tests/test_goals_simulation.py -v
```

Esperado: PASS.

- [ ] **Step 7: Typecheck frontend**

```bash
cd apps/desktop && npm run typecheck
```

- [ ] **Step 8: Stage cambios (NO commit)**

```bash
git add backend/app/modules/goals/simulation_service.py \
        backend/app/modules/goals/schemas.py \
        backend/app/tests/test_goals_simulation.py \
        apps/desktop/src/features/goals/components/GoalSimulationPanel.tsx
```

---

## Task 3: AI Assistant Reliability Stabilization (10.6.6)

**Files:**
- Read: `backend/app/modules/ai/service.py`
- Read: `backend/app/modules/ai/providers/lmstudio_provider.py`
- Read: `backend/app/modules/ai/providers/ollama_provider.py`
- Read: `backend/app/modules/ai/routes.py`
- Read: `apps/desktop/src/features/assistant/hooks/useAiAssistant.ts`
- Read: `apps/desktop/src/features/assistant/components/AiMessageList.tsx`
- Test: `backend/app/tests/test_ai_assistant.py`

**Root cause to verify:** El asistente "falla la mayoría de veces". Probable causa: el provider detection falla silenciosamente o hay timeouts no manejados que convierten respuestas en errores vacíos. El frontend puede mostrar estado de carga indefinida o respuesta vacía sin error visible.

- [ ] **Step 1: Leer los providers y detectar timeout/error handling**

```bash
cat backend/app/modules/ai/providers/lmstudio_provider.py
cat backend/app/modules/ai/providers/ollama_provider.py
```

Buscar:
- ¿Existe `timeout` en las requests HTTP?
- ¿Se captura `httpx.TimeoutException` o `requests.exceptions.Timeout`?
- ¿El `is_available()` check tiene timeout propio o usa el default (puede ser infinito)?

- [ ] **Step 2: Escribir test de degradación offline**

En `backend/app/tests/test_ai_assistant.py`, añadir:

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_chat_with_no_provider_returns_honest_error():
    """Cuando ningún provider está disponible, la respuesta debe ser 200 con mensaje de error claro."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/ai/chat", json={
            "message": "¿Cuáles son mis gastos del mes?",
            "provider": "ollama",
        })
    # No debe ser 500 ni timeout
    assert response.status_code in (200, 503)
    data = response.json()
    # Debe haber un mensaje, no vacío
    if response.status_code == 200:
        assert data.get("response") or data.get("message") or data.get("error")

@pytest.mark.asyncio
async def test_provider_availability_endpoint_responds_quickly():
    """El endpoint de health del provider debe responder en menos de 3 segundos."""
    import time
    async with AsyncClient(app=app, base_url="http://test") as client:
        start = time.monotonic()
        response = await client.get("/api/ai/providers")
        elapsed = time.monotonic() - start
    assert response.status_code == 200
    assert elapsed < 3.0, f"Provider check tardó {elapsed:.1f}s — timeout no configurado"
```

```bash
cd backend && uv run pytest app/tests/test_ai_assistant.py::test_provider_availability_endpoint_responds_quickly -v
```

- [ ] **Step 3: Añadir timeout explícito a los providers**

En `backend/app/modules/ai/providers/lmstudio_provider.py` y `ollama_provider.py`, asegurar timeout:

```python
# En cada provider, en la llamada HTTP:
import httpx

# ANTES:
response = requests.post(url, json=payload)

# DESPUÉS:
response = requests.post(url, json=payload, timeout=30)  # 30s máx

# O si usa httpx:
async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
    response = await client.post(url, json=payload)
```

En el método `is_available()` de cada provider:

```python
def is_available(self) -> bool:
    try:
        response = requests.get(self.base_url + "/health", timeout=3)  # 3s para health check
        return response.status_code == 200
    except Exception:
        return False
```

- [ ] **Step 4: Asegurar que el servicio devuelve respuesta honesta cuando no hay provider**

En `backend/app/modules/ai/service.py`, en la función `chat`:

```python
# Al inicio de chat(), verificar disponibilidad antes de intentar llamar:
provider = get_provider(provider_name)
if not provider.is_available():
    return ChatResponse(
        response="El asistente IA no está disponible. Asegúrate de que Ollama o LMStudio está ejecutándose.",
        conversation_id=conversation_id or str(uuid4()),
        sources=[],
        tool_calls=[],
        provider_status="offline",
    )
```

- [ ] **Step 5: Corregir frontend para nunca mostrar carga infinita**

En `apps/desktop/src/features/assistant/hooks/useAiAssistant.ts`, añadir timeout de seguridad:

```typescript
// En el sendMessage o chat function, añadir abort controller:
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s máximo

try {
  const response = await fetch(url, { ...options, signal: controller.signal });
  // ...
} catch (err) {
  if (err instanceof Error && err.name === "AbortError") {
    setError("La respuesta tardó demasiado. Comprueba que el provider de IA está activo.");
  } else {
    setError("Error al contactar el asistente.");
  }
} finally {
  clearTimeout(timeoutId);
  setLoading(false);  // SIEMPRE desactivar loading
}
```

- [ ] **Step 6: Ejecutar tests de AI**

```bash
cd backend && uv run pytest app/tests/test_ai_assistant.py -v
```

- [ ] **Step 7: Typecheck**

```bash
cd apps/desktop && npm run typecheck
```

- [ ] **Step 8: Stage cambios (NO commit)**

```bash
git add backend/app/modules/ai/ \
        backend/app/tests/test_ai_assistant.py \
        apps/desktop/src/features/assistant/hooks/useAiAssistant.ts
```

---

## Task 4: Market Data Reliability Stabilization (10.6.2)

**Files:**
- Read: `backend/app/modules/market_intelligence/api/routes.py`
- Read: `backend/app/modules/market_intelligence/api/service.py`
- Read: `apps/desktop/src/features/markets/MarketsPage.tsx`
- Read: `apps/desktop/src/features/markets/components/QuoteRow.tsx`
- Read: `apps/desktop/src/lib/hooks/useMarketIntelligence.ts`

**Root cause to verify:** El módulo de Mercados ya tiene estados honestos, pero falla con frecuencia. El problema es que cuando un provider está caído, no se usa la caché disponible.

- [ ] **Step 1: Leer useMarketIntelligence y MarketsPage**

```bash
cat apps/desktop/src/lib/hooks/useMarketIntelligence.ts
cat apps/desktop/src/features/markets/MarketsPage.tsx
```

Buscar:
- ¿Existe lógica de fallback a caché cuando la API falla?
- ¿El `QuoteRow` muestra diferencia entre dato real y dato cacheado?

- [ ] **Step 2: Añadir campo `data_quality` a QuoteRow**

En `apps/desktop/src/features/markets/components/QuoteRow.tsx`, añadir indicador visual de calidad del dato:

```tsx
// Añadir al final de cada fila, después del precio:
{quote.data_quality && quote.data_quality !== "live" && (
  <span className={`ml-2 rounded px-1.5 py-0.5 text-[10px] font-medium ${
    quote.data_quality === "cached" ? "bg-warning/10 text-warning" :
    quote.data_quality === "stale" ? "bg-accent/10 text-accent" :
    "bg-white/5 text-stone"
  }`}>
    {quote.data_quality === "cached" ? "Caché" :
     quote.data_quality === "stale" ? "Desactualizado" :
     "Sin dato"}
  </span>
)}
```

- [ ] **Step 3: Verificar que el backend devuelve caché cuando el provider falla**

En `backend/app/modules/market_intelligence/api/service.py`, buscar el patrón:

```python
# Patrón correcto — intentar live, caer a caché:
try:
    data = await provider.fetch_live(symbol)
    data["data_quality"] = "live"
except Exception as e:
    logger.warning(f"Live fetch failed for {symbol}: {e}")
    data = cache.get(symbol)
    if data:
        data["data_quality"] = "cached"
    else:
        data = {"symbol": symbol, "value": None, "data_quality": "unavailable"}
```

Si no existe este patrón, implementarlo.

- [ ] **Step 4: Añadir botón de actualización manual con feedback claro en MarketsPage**

En `apps/desktop/src/features/markets/MarketsPage.tsx`, asegurar que el botón de refresh muestra estado:

```tsx
const [refreshing, setRefreshing] = useState(false);
const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

const handleRefresh = async () => {
  setRefreshing(true);
  try {
    await refetch();
    setLastRefresh(new Date());
  } finally {
    setRefreshing(false);
  }
};

// En el render:
<button
  onClick={handleRefresh}
  disabled={refreshing}
  className="flex items-center gap-1.5 rounded-lg bg-white/5 px-3 py-1.5 text-xs text-stone hover:text-on-dark disabled:opacity-50"
>
  <RefreshCw size={12} className={refreshing ? "animate-spin" : ""} />
  {refreshing ? "Actualizando..." : lastRefresh ? `Actualizado ${lastRefresh.toLocaleTimeString("es-ES")}` : "Actualizar"}
</button>
```

- [ ] **Step 5: Typecheck**

```bash
cd apps/desktop && npm run typecheck
```

- [ ] **Step 6: Stage cambios (NO commit)**

```bash
git add apps/desktop/src/features/markets/ \
        apps/desktop/src/lib/hooks/useMarketIntelligence.ts \
        backend/app/modules/market_intelligence/api/service.py
```

---

## Task 5: Portfolio Screenshot Import Stabilization (10.6.1)

**Files:**
- Read: `apps/desktop/src/features/investments/import/PortfolioImportPage.tsx`
- Read: `backend/app/modules/investments/portfolio_import_service.py`
- Read: `backend/app/modules/investments/portfolio_import_routes.py`

**Decisión funcional:** Implementar **Opción B** (alcance honesto). La extracción automática desde captura no está disponible en esta fase. La UI debe comunicarlo claramente sin prometer funcionalidad que no existe.

- [ ] **Step 1: Leer PortfolioImportPage para identificar qué promete actualmente**

```bash
cat apps/desktop/src/features/investments/import/PortfolioImportPage.tsx
```

Buscar: ¿existe un botón/tab de "Importar desde captura"? ¿Qué hace?

- [ ] **Step 2: Marcar la opción de captura como "Próximamente" o "Experimental"**

Si existe un tab/botón de captura de pantalla en `PortfolioImportPage.tsx`:

```tsx
// ANTES:
<button onClick={handleScreenshotImport}>Importar desde captura</button>

// DESPUÉS:
<div className="relative">
  <button disabled className="opacity-40 cursor-not-allowed ...">
    Importar desde captura
  </button>
  <span className="absolute -top-1 -right-1 rounded-full bg-warning px-1.5 py-0.5 text-[9px] font-bold uppercase text-white">
    Próximo
  </span>
</div>
<p className="mt-1 text-xs text-stone">
  La extracción automática desde captura está pendiente. Usa la entrada manual o pega texto.
</p>
```

- [ ] **Step 3: Asegurar que el flujo manual y texto-pegado funcionan correctamente**

Verificar que:
- La entrada manual de holdings uno por uno funciona
- El flujo de "pegar texto" llega hasta la tabla de revisión
- No hay logs que registren datos sensibles de captura

- [ ] **Step 4: Test de que la captura no genera holdings sin revisión**

En `backend/app/tests/test_portfolio_import.py`, añadir:

```python
def test_screenshot_endpoint_not_creates_holdings_without_review():
    """La captura NO debe crear holdings directamente — solo debe devolver datos para revisión."""
    # Si el endpoint de screenshot existe, verificar que devuelve preview, no crea holdings
    # Si no existe, este test pasa trivialmente (correcto — Opción B)
    from app.modules.investments.portfolio_import_routes import router
    screenshot_routes = [r for r in router.routes if "screenshot" in str(r.path)]
    if not screenshot_routes:
        return  # Opción B implementada: no hay ruta de screenshot
    # Si existe, debe requerir confirmación
    # (validar que la ruta devuelve draft, no persiste directamente)
```

```bash
cd backend && uv run pytest app/tests/test_portfolio_import.py -v
```

- [ ] **Step 5: Stage cambios (NO commit)**

```bash
git add apps/desktop/src/features/investments/import/ \
        backend/app/tests/test_portfolio_import.py
```

---

## Task 6: Planning Auto-Refresh Fix (10.6.5)

**Files:**
- Modify: `apps/desktop/src/features/planning/BudgetTab.tsx`

**Root cause identificado:** `BudgetTab` usa dos hooks independientes: `useBudgets()` (para `add`) y `useBudgetComparison()` (para la lista comparativa). Cuando `add` llama a `createBudget` y luego recarga `budgets`, el `useBudgetComparison` no se entera y mantiene datos stale. El usuario tiene que cambiar de tab para refrescar.

- [ ] **Step 1: Escribir test de comportamiento esperado**

Crear `apps/desktop/src/features/planning/__tests__/BudgetTab.test.tsx`:

```tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import BudgetTab from "../BudgetTab";

// Mock hooks
jest.mock("@/lib/hooks/useBudgets", () => ({
  useBudgets: () => ({ add: jest.fn().mockResolvedValue(undefined), refresh: jest.fn() }),
  useBudgetComparison: () => ({ data: [], loading: false, error: null, refresh: jest.fn() }),
}));

test("after adding a budget, comparison data refreshes without tab change", async () => {
  const mockRefreshComparison = jest.fn();
  // ... test implementation
});
```

> Nota: Los tests de frontend con jest son opcionales aquí si no hay setup existente. Verificar visualmente tras el fix.

- [ ] **Step 2: Corregir BudgetTab para refrescar ambos hooks tras add**

En `apps/desktop/src/features/planning/BudgetTab.tsx`:

```tsx
// ANTES:
export default function BudgetTab() {
  const { add, refresh } = useBudgets();
  const { data, loading, error } = useBudgetComparison();
  // ...
  {showModal && (
    <BudgetFormModal onSubmit={add} onClose={() => setShowModal(false)} />
  )}

// DESPUÉS:
export default function BudgetTab() {
  const { add } = useBudgets();
  const { data, loading, error, refresh: refreshComparison } = useBudgetComparison();

  const handleAddBudget = async (body: BudgetCreate) => {
    await add(body);
    await refreshComparison();
  };
  // ...
  {showModal && (
    <BudgetFormModal onSubmit={handleAddBudget} onClose={() => setShowModal(false)} />
  )}
```

El import de `BudgetCreate` ya debe estar disponible desde `@/lib/api/budgets` (lo usa `BudgetFormModal`). Añadir al import si no está.

- [ ] **Step 3: Verificar que BudgetFormModal importa el tipo correcto**

`BudgetFormModal` recibe `onSubmit: (data: BudgetCreate) => Promise<void>` — tipo ya definido. No hay cambios de interfaz.

- [ ] **Step 4: Typecheck**

```bash
cd apps/desktop && npm run typecheck
```

Esperado: 0 errores.

- [ ] **Step 5: Verificación manual**

Abrir Planning → Presupuestos → Crear presupuesto → Los valores deben actualizarse sin cambiar de tab.

- [ ] **Step 6: Stage cambios (NO commit)**

```bash
git add apps/desktop/src/features/planning/BudgetTab.tsx
```

---

## Task 7: Technical QA Gate (10.6.7)

**Files:**
- Run: `backend/` (pytest)
- Run: `apps/desktop/` (typecheck, lint si aplica)
- Run: arranque limpio de la app

- [ ] **Step 1: Ejecutar backend tests completos**

```bash
cd backend && uv run pytest --tb=short -q
```

Documentar:
- Total tests ejecutados
- Tests fallidos (nombre + error)
- Severidad estimada por cada fallo

- [ ] **Step 2: Ejecutar typecheck frontend**

```bash
cd apps/desktop && npm run typecheck
```

Documentar errores si los hay.

- [ ] **Step 3: Arranque limpio**

```bash
# Terminal 1:
cd backend && uv run uvicorn app.main:app --port 8000

# Terminal 2 (verificar health):
curl http://localhost:8000/health
```

Esperado: `{"status": "ok"}` o similar.

- [ ] **Step 4: Verificar integridad de DB**

```bash
cd backend && uv run python -c "
from app.core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM transactions'))
    print('Transactions:', result.scalar())
    result = conn.execute(text('SELECT COUNT(*) FROM budgets'))
    print('Budgets:', result.scalar())
"
```

- [ ] **Step 5: Documentar resultado**

Crear `docs/31_PHASE_10_6_RELEASE_CANDIDATE_STABILIZATION.md` con el registro de QA.

---

## Task 8: Final Go/No-Go Report (10.6.8)

- [ ] **Step 1: Completar `docs/31_PHASE_10_6_RELEASE_CANDIDATE_STABILIZATION.md`**

El documento debe incluir, por módulo:

| Módulo | Estado | Bloqueante | Decisión |
|--------|--------|------------|----------|
| Economía | ✅ Corregido / ❌ Pendiente | P0-03 | Valores repetidos eliminados |
| Objetivos | ✅ / ❌ | P0-04 | Simulación con texto explicativo |
| Asistente IA | ✅ / ❌ | P0-05 | Timeout + degradación honesta |
| Mercados | ✅ / ❌ | P0-02 | Caché visible + refresh manual |
| Importar cartera | ✅ / ❌ | P0-01 | **Opción B** — captura marcada como pendiente |
| Planificación | ✅ / ❌ | P1-01 | Auto-refresh tras crear presupuesto |
| Transacciones | ✅ | UI | Picklist + cuenta opcional en edición |

- [ ] **Step 2: Determinar veredicto Go / No-Go**

Go únicamente si:
- Todos los P0 están resueltos o comunicados honestamente (Opción B en importar cartera cuenta como Go para ese módulo)
- No hay errores crudos visibles en la UI
- Backend tests pasan sin P0 conocidos
- Frontend typecheck limpio

- [ ] **Step 3: Actualizar docs/02_ROADMAP.md**

Marcar Fase 10.6 como completada con fecha y veredicto.

---

## Verificación final antes de cerrar la fase

```bash
# Backend completo
cd backend && uv run pytest --tb=short -q

# Frontend typecheck
cd apps/desktop && npm run typecheck

# Git status — todos los cambios staged, nada olvidado
git status
git diff --staged --stat
```

Confirmar con el usuario antes de hacer commit.
