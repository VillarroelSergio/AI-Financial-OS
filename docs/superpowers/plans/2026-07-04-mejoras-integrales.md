# Mejoras Integrales AI-Financial-OS — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corregir los bugs de importación detectados, añadir autenticación local al backend, eliminar los cuellos de botella de rendimiento, hacer visibles/fiables los datos de mercado y pulir el flujo de importación y el dashboard.

**Architecture:** Backend FastAPI + SQLite (migraciones ligeras en `create_tables()`) + DuckDB para analítica de mercado. Frontend Tauri + React 18 + TypeScript. Cada tarea es autocontenida y deja el software funcionando. Las migraciones de esquema siguen el patrón existente de `_migrate_*` en `backend/app/core/database.py` (NO Alembic).

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy / pytest · React 18 / TypeScript / Vite · Rust (Tauri) solo en Tarea 5.

## Global Constraints

- **Idioma español en toda la UI** (restricción de proyecto).
- **Local-first absoluto**: nada de cloud para datos personales.
- **No sobrecargar la UI**; mantener estilo Dark Premium.
- **Commits: NUNCA automáticos.** Cada paso de "commit" significa: `git add` de los ficheros y **pedir confirmación explícita al usuario** antes de ejecutar `git commit`. Si el ejecutor es un subagente que no puede preguntar, solo stage — el commit lo hace el usuario en el checkpoint.
- **Tests**: la aprobación de este plan autoriza a ejecutar únicamente los comandos `pytest`/`tsc` listados en los pasos. No ejecutar suites completas no listadas sin permiso.
- **Tras cambios de UI** (Tareas 13 y 16): ejecutar `npm run ux:snapshots:headed` desde `apps/desktop` antes de cerrar la tarea.
- Comandos backend se ejecutan desde `AI-Financial-OS/backend` con el venv activo (`.venv/Scripts/python -m pytest ...` en Windows).
- Todas las rutas de este plan son relativas a `d:/FinancialAgent/AI-Financial-OS/`.

**Decisiones de alcance (descartado deliberadamente):**
- Alembic: el patrón `_migrate_*` existente cubre las 3 columnas nuevas de este plan.
- TanStack Query: se implementa caché TTL de ~30 líneas en `client.ts`; migrar a TanStack Query solo si el caché simple se queda corto.
- Cifrado SQLCipher: fuera de alcance; el token de API (Tarea 5) cubre el riesgo principal.
- Cambio de modelo IA por defecto (`qwen3-coder:30b`): no se toca — es el setup local funcionando del usuario.
- Framework de tests frontend (vitest): no se añade; la lógica nueva de frontend es trivial y se verifica con `tsc` + snapshots UX.
- Virtualización de la tabla de Transacciones: la paginación backend (Tarea 7) elimina el caso doloroso; virtualizar solo si con datos reales la tabla sigue lenta.

---

## FASE 1 — Correctitud de importación

### Task 1: Rollback revierte las HouseholdBills del batch

**Files:**
- Modify: `backend/app/models/household_bill.py` (añadir columna)
- Modify: `backend/app/core/database.py` (migración ligera)
- Modify: `backend/app/modules/imports/routes.py:234-246` (confirm) y `:297-308` (rollback)
- Test: `backend/app/tests/test_imports.py` (añadir test)

**Interfaces:**
- Produces: columna `HouseholdBill.import_batch_id: str | None`; rollback borra bills con ese batch_id.

- [ ] **Step 1: Escribir el test que falla**

Añadir a `backend/app/tests/test_imports.py`:

```python
def test_rollback_removes_household_bills(client):
    csv = (
        "date,amount,description\n"
        "01/03/2026,-55.30,Adeudo recibo Iberdrola electricidad\n"
    )
    preview = client.post(
        "/api/imports/preview",
        files={"file": ("recibos.csv", csv.encode(), "text/csv")},
    )
    assert preview.status_code == 200
    batch_id = preview.json()["import_batch_id"]

    confirm = client.post(f"/api/imports/{batch_id}/confirm", json={})
    assert confirm.status_code == 200
    assert confirm.json()["bills_created"] == 1
    assert len(client.get("/api/household-bills").json()) == 1

    rollback = client.post(f"/api/imports/{batch_id}/rollback")
    assert rollback.status_code == 200
    assert client.get("/api/household-bills").json() == []
```

Nota: si el mapping genérico del preview no mapea `description` (solo mapea `date` y `amount` cuando no hay perfil), pasar el mapping explícito en el confirm: `json={"mapping": {"date": "date", "amount": "amount", "description": "description"}}` — comprobar primero qué devuelve `preview.json()["mapping"]` y ajustar el test a la realidad, no al revés.

- [ ] **Step 2: Ejecutar el test y verificar que falla**

Run: `python -m pytest app/tests/test_imports.py::test_rollback_removes_household_bills -v`
Expected: FAIL en el último assert (la bill sobrevive al rollback).

- [ ] **Step 3: Implementación**

En `backend/app/models/household_bill.py`, tras `category_id`:

```python
    import_batch_id: Mapped[str | None] = mapped_column(String, nullable=True)
```

En `backend/app/core/database.py`, dentro de `create_tables()` tras `_migrate_transactions_scope()`:

```python
    _migrate_household_bills_batch()
```

y al final del fichero:

```python
def _migrate_household_bills_batch() -> None:
    """Enlaza facturas detectadas con su importación para poder revertirlas."""
    with engine.begin() as connection:
        cols = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(household_bills)")}
        if cols and "import_batch_id" not in cols:
            connection.exec_driver_sql(
                "ALTER TABLE household_bills ADD COLUMN import_batch_id TEXT"
            )
```

En `backend/app/modules/imports/routes.py`, en el constructor de `HouseholdBill(...)` del confirm (línea ~235), añadir:

```python
                        import_batch_id=batch.id,
```

En el endpoint `rollback`, tras el delete de transacciones:

```python
    bills_removed = (
        db.query(HouseholdBill).filter(HouseholdBill.import_batch_id == batch_id).delete()
    )
```

y añadir `"bills_removed": bills_removed` al dict de retorno.

- [ ] **Step 4: Verificar que pasa**

Run: `python -m pytest app/tests/test_imports.py -v`
Expected: PASS todos (el resto de tests de imports no deben romperse).

- [ ] **Step 5: Stage + confirmación de commit**

```bash
git add backend/app/models/household_bill.py backend/app/core/database.py backend/app/modules/imports/routes.py backend/app/tests/test_imports.py
```
Pedir confirmación al usuario: `fix(imports): rollback también revierte las facturas detectadas`

---

### Task 2: Hash de duplicados con índice de ocurrencia

Dos movimientos idénticos el mismo día (dos cafés de 1,50 €) hoy colisionan y el segundo se descarta como duplicado. Se añade un índice de ocurrencia **dentro del archivo**: la primera ocurrencia mantiene el hash actual (retrocompatible con datos ya importados), la n-ésima añade `|n` a la clave.

**Files:**
- Modify: `backend/app/modules/imports/service.py:167-227` (`normalize_row`)
- Modify: `backend/app/modules/imports/routes.py` (bucles de preview y confirm)
- Test: `backend/app/tests/test_imports.py`

**Interfaces:**
- Produces: `normalize_row(raw, mapping, profile=None, occurrence=0)` — con `occurrence=0` el hash es idéntico al actual.
- Consumes: los bucles de preview y confirm iteran las filas en el mismo orden, por lo que el contador de ocurrencias produce los mismos hashes en ambos.

- [ ] **Step 1: Test que falla**

```python
def test_repeated_identical_rows_import_both(client):
    csv = (
        "date,amount,description\n"
        "01/03/2026,-1.50,Cafeteria Sol\n"
        "01/03/2026,-1.50,Cafeteria Sol\n"
    )
    preview = client.post(
        "/api/imports/preview",
        files={"file": ("cafes.csv", csv.encode(), "text/csv")},
    )
    body = preview.json()
    assert body["rows_valid"] == 2  # la segunda NO es duplicado

    confirm = client.post(f"/api/imports/{body['import_batch_id']}/confirm", json={})
    assert confirm.json()["rows_imported"] == 2
```

- [ ] **Step 2: Verificar que falla**

Run: `python -m pytest app/tests/test_imports.py::test_repeated_identical_rows_import_both -v`
Expected: FAIL (`rows_valid == 1` o `rows_imported == 1`).

Nota: si el preview marca la segunda fila como `duplicate` solo contra la BD (no dentro del archivo), el test puede pasar en preview y fallar en una segunda importación. Si `rows_valid == 2` ya en el estado actual, ampliar el test: confirmar, volver a hacer preview del mismo archivo y comprobar que ambas filas salen `duplicate` (2), y con un archivo de 3 cafés idénticos el tercero sale `valid`. Ajustar al comportamiento real antes de implementar.

- [ ] **Step 3: Implementación**

En `service.py`, cambiar la firma y la clave de duplicado:

```python
def normalize_row(
    raw: dict[str, str],
    mapping: dict[str, str | None],
    profile: FormatProfile | None = None,
    occurrence: int = 0,
) -> tuple[dict, list[str], list[str]]:
```

y al final, sustituir el cálculo de `duplicate_key`:

```python
    duplicate_key = "|".join(
        [date, str(amount), description.casefold().strip(), category.casefold().strip()]
    )
    # Ocurrencia n>0 dentro del mismo archivo: sufijo para no colisionar con la
    # primera. La ocurrencia 0 conserva el hash histórico (retrocompatible).
    if occurrence:
        duplicate_key += f"|{occurrence}"
    normalized["duplicate_hash"] = hashlib.sha256(duplicate_key.encode()).hexdigest()
```

En `routes.py`, en el bucle del **preview** (línea ~69), llevar un contador por el hash de ocurrencia 0 y re-normalizar solo cuando hay colisión dentro del archivo:

```python
    occurrence_counts: dict[str, int] = {}
    for number, raw in enumerate(rows, 2):
        skipped_reason = None
        if profile and profile.status_column:
            state = raw.get(profile.status_column, "").strip().upper()
            if state and state not in profile.status_allowed:
                skipped_reason = f"Operación no completada ({state})"
        normalized, errors, warnings = normalize_row(raw, mapping, profile)
        base_hash = normalized["duplicate_hash"]
        occ = occurrence_counts.get(base_hash, 0)
        occurrence_counts[base_hash] = occ + 1
        if occ:
            normalized, errors, warnings = normalize_row(raw, mapping, profile, occurrence=occ)
        ...
```

Aplicar exactamente el mismo patrón de contador en el bucle del **confirm** (línea ~160), que re-normaliza las filas en el mismo orden:

```python
    occurrence_counts: dict[str, int] = {}
    for row in rows:
        raw = json.loads(row.raw_payload_json)
        normalized, errors, _ = normalize_row(raw, mapping, profile)
        base_hash = normalized["duplicate_hash"]
        occ = occurrence_counts.get(base_hash, 0)
        occurrence_counts[base_hash] = occ + 1
        if occ:
            normalized, errors, _ = normalize_row(raw, mapping, profile, occurrence=occ)
        if errors or row.status != "valid":
            continue
        ...
```

Importante: el contador del confirm debe incrementarse para **todas** las filas (también las inválidas/skipped), igual que en preview, para que los índices coincidan.

- [ ] **Step 4: Verificar**

Run: `python -m pytest app/tests/test_imports.py -v`
Expected: PASS todos.

- [ ] **Step 5: Stage + confirmación de commit**

```bash
git add backend/app/modules/imports/service.py backend/app/modules/imports/routes.py backend/app/tests/test_imports.py
```
Mensaje propuesto: `fix(imports): movimientos idénticos el mismo día ya no se descartan como duplicados`

---

### Task 3: Auto-categorizador — tokens exactos para palabras cortas

`"dia"` casa por prefijo con "diagnóstico"/"diario", `"suma"` con "sumario", `"bar"` con "Barcelona". Las palabras genéricas cortas pasan a exigir token exacto; los prefijos intencionados ("pizz" → pizzería, "cine" → Cinesur) se mantienen.

**Files:**
- Modify: `backend/app/modules/imports/auto_categorizer.py`
- Test: `backend/app/tests/test_imports.py` (o el fichero donde vivan los tests del categorizador — buscar `auto_category` en `app/tests/` primero y añadir junto a los existentes)

- [ ] **Step 1: Test que falla**

```python
from app.modules.imports.auto_categorizer import auto_category


def test_short_keywords_require_exact_token():
    # Falsos positivos actuales por prefijo
    assert auto_category("Centro de diagnostico medico") != "Alimentación"
    assert auto_category("Sumario judicial") != "Alimentación"
    assert auto_category("Hotel Barcelona Centro") == "Ocio"  # "hotel" gana, no "bar"
    assert auto_category("Barbería Paco") != "Restaurante"
    # Los aciertos existentes no se rompen
    assert auto_category("SUPERMERCADOS DIA MADRID") == "Alimentación"
    assert auto_category("Bar Manolo") == "Restaurante"
    assert auto_category("Cinesur Nervion") == "Ocio"
    assert auto_category("Pizzeria Napoli") == "Restaurante"
```

- [ ] **Step 2: Verificar que falla**

Run: `python -m pytest app/tests/ -k short_keywords -v`
Expected: FAIL en "diagnostico", "Sumario" o "Barbería".

- [ ] **Step 3: Implementación**

En `auto_categorizer.py`, añadir tras `KEYWORD_CATEGORIES`:

```python
# Palabras genéricas cortas que solo casan como token exacto: por prefijo
# producen falsos positivos ("dia" → "diagnóstico", "bar" → "Barbería").
EXACT_TOKEN_KEYWORDS = {"dia", "suma", "bar", "cafe", "film", "disco", "metro", "emt"}
```

y en `auto_category`, cambiar la rama de una sola palabra:

```python
        elif keyword in EXACT_TOKEN_KEYWORDS:
            if keyword in tokens:
                return category
        elif any(token.startswith(keyword) for token in tokens):
            return category
```

- [ ] **Step 4: Verificar**

Run: `python -m pytest app/tests/ -k "short_keywords or categor" -v`
Expected: PASS. Si algún test existente del categorizador dependía del prefijo de una palabra del set (p. ej. "cafes"), evaluar si el test describía un falso positivo (actualizar test) o un caso real (sacar esa palabra del set).

- [ ] **Step 5: Stage + confirmación de commit**

```bash
git add backend/app/modules/imports/auto_categorizer.py backend/app/tests/
```
Mensaje: `fix(imports): keywords cortas del categorizador exigen token exacto`

---

### Task 4: Emparejado de traspasos exige indicio de traspaso

Hoy cualquier par importe-opuesto en cuentas distintas ±3 días se convierte en transfer (una nómina de 1.200 € y un alquiler de −1.200 € se anularían). Se exige que **al menos uno** de los dos movimientos tenga descripción con pinta de traspaso.

**Files:**
- Modify: `backend/app/modules/imports/routes.py:252-282`
- Test: `backend/app/tests/test_imports.py`

- [ ] **Step 1: Test que falla**

```python
def _import_csv(client, filename, csv_text, mapping=None):
    preview = client.post(
        "/api/imports/preview",
        files={"file": (filename, csv_text.encode(), "text/csv")},
    )
    batch_id = preview.json()["import_batch_id"]
    confirm = client.post(f"/api/imports/{batch_id}/confirm", json=(mapping or {}))
    return confirm.json()


def test_opposite_amounts_without_transfer_hint_stay_income_expense(client):
    # Cuenta A: nómina. Cuenta B: alquiler del mismo importe. NO es un traspaso.
    result = _import_csv(
        client,
        "mix.csv",
        "date,account,amount,description\n"
        "01/03/2026,Banco A,1200.00,Nomina empresa SL\n"
        "02/03/2026,Banco B,-1200.00,Alquiler marzo piso\n",
    )
    assert result["transfers_detected"] == 0


def test_opposite_amounts_with_transfer_hint_are_paired(client):
    result = _import_csv(
        client,
        "traspaso.csv",
        "date,account,amount,description\n"
        "01/03/2026,Banco A,-500.00,Traspaso a Revolut\n"
        "01/03/2026,Revolut,500.00,Recarga desde Banco A\n",
    )
    assert result["transfers_detected"] == 1
```

Nota: comprobar que el mapping genérico del preview incluye `account` y `description`; si no, pasar mapping explícito en el confirm como en la Task 1.

- [ ] **Step 2: Verificar que falla**

Run: `python -m pytest app/tests/test_imports.py -k transfer_hint -v`
Expected: el primer test FALLA (`transfers_detected == 1`).

- [ ] **Step 3: Implementación**

En `routes.py`, antes del bucle de emparejado, añadir:

```python
import re as _re

_TRANSFER_HINT = _re.compile(
    r"traspaso|transferencia|transfer|recarga|top.?up|revolut|bizum enviado"
    r"|savings vault|^to |^from |envio a|enviado a",
    _re.IGNORECASE,
)


def _looks_like_transfer(description: str) -> bool:
    return bool(_TRANSFER_HINT.search(description))
```

(colocar el regex y el helper a nivel de módulo, junto a `fail`, no dentro del endpoint)

y en el bucle, tras encontrar `counterpart`:

```python
        if counterpart is not None and (
            _looks_like_transfer(tx.description) or _looks_like_transfer(counterpart.description)
        ):
            tx.type = "transfer"
            ...
```

(la condición sustituye al `if counterpart is not None:` actual; el cuerpo no cambia)

Actualizar el comentario `ponytail:` existente: `# ponytail: emparejado por importe exacto + indicio textual; si aparecen traspasos sin indicio, pasar a confirmación manual en el preview.`

- [ ] **Step 4: Verificar**

Run: `python -m pytest app/tests/test_imports.py app/tests/test_reconciliation.py -v`
Expected: PASS. Si algún test existente creaba traspasos sin indicio textual, revisar si describía el falso positivo — actualizarlo con descripción de traspaso realista.

- [ ] **Step 5: Stage + confirmación de commit**

```bash
git add backend/app/modules/imports/routes.py backend/app/tests/test_imports.py
```
Mensaje: `fix(imports): el emparejado de traspasos exige indicio textual de traspaso`

---

## FASE 2 — Seguridad

### Task 5: Token de API para el backend local

Cualquier proceso local puede hoy leer/modificar los datos financieros vía `127.0.0.1:8010`. Se añade un token compartido: Tauri lo genera por sesión, lo pasa al backend por env var y al frontend vía comando Tauri. Sin token en el entorno (desarrollo con `python run_server.py` + vite), el middleware no exige nada — fricción cero en dev.

**Files:**
- Modify: `backend/app/main.py` (middleware)
- Modify: `apps/desktop/src-tauri/src/lib.rs` (generar token, env, comando)
- Modify: `apps/desktop/src/lib/api/client.ts` (header)
- Test: `backend/app/tests/test_security_token.py` (nuevo)

**Interfaces:**
- Produces: env var `FINOS_API_TOKEN`; header `X-Api-Token`; comando Tauri `get_api_token() -> String`.

- [ ] **Step 1: Test que falla**

Crear `backend/app/tests/test_security_token.py`:

```python
import os

from fastapi.testclient import TestClient


def test_requests_without_token_rejected_when_token_set(client, monkeypatch):
    monkeypatch.setenv("FINOS_API_TOKEN", "secreto123")
    assert client.get("/api/accounts").status_code == 401
    assert client.get("/health").status_code == 200  # health queda abierto para el launcher
    ok = client.get("/api/accounts", headers={"X-Api-Token": "secreto123"})
    assert ok.status_code == 200


def test_requests_allowed_when_no_token_configured(client, monkeypatch):
    monkeypatch.delenv("FINOS_API_TOKEN", raising=False)
    assert client.get("/api/accounts").status_code == 200
```

- [ ] **Step 2: Verificar que falla**

Run: `python -m pytest app/tests/test_security_token.py -v`
Expected: FAIL primer test (401 esperado, llega 200).

- [ ] **Step 3: Implementación backend**

En `backend/app/main.py`, tras el bloque CORS:

```python
import os

from fastapi import Request
from fastapi.responses import JSONResponse


@app.middleware("http")
async def require_api_token(request: Request, call_next):
    # Solo se exige si el launcher configuró token (producción empaquetada).
    # /health queda abierto: el launcher lo usa para saber cuándo está listo.
    token = os.environ.get("FINOS_API_TOKEN")
    if token and request.url.path != "/health" and request.method != "OPTIONS":
        if request.headers.get("x-api-token") != token:
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "UNAUTHORIZED", "message": "Token de API inválido", "details": {}}},
            )
    return await call_next(request)
```

Se lee de `os.environ` en cada request (no de `settings`) para que sea testeable con monkeypatch y para no cachear un token que el launcher inyecta después del import.

- [ ] **Step 4: Verificar backend**

Run: `python -m pytest app/tests/test_security_token.py app/tests/test_health.py -v`
Expected: PASS.

- [ ] **Step 5: Implementación Tauri (Rust)**

En `apps/desktop/src-tauri/src/lib.rs`:

1. Generar el token en `run()` antes del builder (sin dependencia nueva de crates — timestamp + direcciones aleatorias del sistema no son criptográficas; usar el crate `uuid` **solo si ya está** en `Cargo.toml`; si no, leer 32 bytes de `/dev/urandom` no existe en Windows → usar dos `Instant`/`SystemTime` NO es aceptable para un token. Comprobar `Cargo.toml`: tauri ya depende de `getrandom` transitivamente; añadir `getrandom = "0.2"` como dependencia directa es aceptable por ser ya parte del árbol):

```rust
fn generate_token() -> String {
    let mut bytes = [0u8; 32];
    getrandom::getrandom(&mut bytes).expect("no hay fuente de aleatoriedad");
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

#[tauri::command]
fn get_api_token(state: tauri::State<ApiToken>) -> String {
    state.0.clone()
}

struct ApiToken(String);
```

2. En `run()`:

```rust
pub fn run() {
    let token = generate_token();
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(ApiToken(token.clone()))
        .invoke_handler(tauri::generate_handler![get_api_token])
        .setup(move |_app| {
            #[cfg(not(debug_assertions))]
            {
                use tauri::Manager;
                let resource_dir = _app.path().resource_dir()?;
                if let Some(child) = backend::spawn(&resource_dir, &token)
                    .map_err(std::io::Error::other)?
                {
                    _app.manage(backend::BackendProcess(std::sync::Mutex::new(Some(child))));
                }
                backend::wait_until_healthy().map_err(std::io::Error::other)?;
            }
            #[cfg(debug_assertions)]
            let _ = &token;
            Ok(())
        })
        ...
```

3. `backend::spawn` acepta el token:

```rust
    pub fn spawn(resource_dir: &std::path::Path, token: &str) -> Result<Option<Child>, String> {
        if health_ok() {
            return Ok(None);
        }
        let exe = resource_dir.join("backend").join("financial-backend.exe");
        let mut cmd = Command::new(&exe);
        cmd.current_dir(exe.parent().unwrap())
            .env("APP_ENV", "production")
            .env("BACKEND_PORT", PORT.to_string())
            .env("FINOS_API_TOKEN", token);
        ...
```

Caso borde: si `spawn` encuentra un backend ya vivo (`health_ok()` → `Ok(None)`), ese backend tiene **otro** token y la app no podrá hablar con él. Aceptable: es el mismo escenario degradado que hoy (proceso duplicado); documentarlo con un comentario en `spawn`.

- [ ] **Step 6: Implementación frontend**

En `apps/desktop/src/lib/api/client.ts`:

```typescript
import { getMockResponse } from "./mock-data";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8010";
const USE_MOCK = import.meta.env.VITE_USE_MOCK_DATA === "true";

let apiToken: string | null = null;
// En Tauri empaquetado el launcher expone el token; en dev (navegador/vite) no hay
// token y el backend tampoco lo exige.
const tokenReady: Promise<void> = (async () => {
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    apiToken = await invoke<string>("get_api_token");
  } catch {
    apiToken = null;
  }
})();

async function request<T>(path: string, init?: RequestInit, signal?: AbortSignal): Promise<T> {
  if (USE_MOCK) {
    return Promise.resolve(getMockResponse<T>(path, init));
  }
  await tokenReady;
  const isFormData = init?.body instanceof FormData;
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(apiToken ? { "X-Api-Token": apiToken } : {}),
      ...init?.headers,
    },
    ...init,
    ...(signal ? { signal } : {}),
  });
  // ... resto sin cambios
```

- [ ] **Step 7: Verificar compilación completa**

Run (desde `apps/desktop`): `npx tsc --noEmit` y (desde `apps/desktop/src-tauri`) `cargo check`
Expected: sin errores. La verificación end-to-end real del token requiere build empaquetada — anotar en el PR/commit que se validó backend por test + compilación de ambos lados.

- [ ] **Step 8: Stage + confirmación de commit**

```bash
git add backend/app/main.py backend/app/tests/test_security_token.py apps/desktop/src-tauri/src/lib.rs apps/desktop/src-tauri/Cargo.toml apps/desktop/src/lib/api/client.ts
```
Mensaje: `feat(security): token de sesión entre launcher, backend y frontend`

---

### Task 6: Rotación de backups

**Files:**
- Modify: `backend/app/modules/security/service.py:29-42`
- Test: `backend/app/tests/test_accounts_purge.py` o nuevo `backend/app/tests/test_backups.py`

- [ ] **Step 1: Test que falla**

Crear `backend/app/tests/test_backups.py`:

```python
from app.modules.security import service


def test_create_backup_keeps_last_20(client, tmp_path, monkeypatch):
    db_file = tmp_path / "financial.db"
    db_file.write_bytes(b"fake sqlite")
    monkeypatch.setattr(service, "database_path", lambda url=None: db_file)

    for i in range(25):
        result = service.create_backup()
        # nombres únicos aunque el timestamp coincida en el mismo segundo
        (tmp_path / "backups" / result["filename"]).touch()

    backups = service.list_backups()
    assert len(backups) <= 20
```

Nota: `create_backup` nombra por timestamp con resolución de segundo — 25 llamadas en bucle colisionan. Si el test resulta frágil por eso, crear los 25 ficheros a mano con `(backup_dir / f"financial-2026010{i:02d}T000000Z.db").write_bytes(b"x")` y llamar a `create_backup()` una vez, comprobando que purga.

- [ ] **Step 2: Verificar que falla**

Run: `python -m pytest app/tests/test_backups.py -v`
Expected: FAIL (`len > 20`).

- [ ] **Step 3: Implementación**

En `security/service.py`, añadir al final de `create_backup` antes del `return`:

```python
    _prune_backups(keep=20)
```

y la función:

```python
def _prune_backups(keep: int) -> None:
    """Retiene los `keep` backups más recientes; el resto se borra."""
    paths = sorted(backup_dir().glob("financial-*.db"), reverse=True)
    for path in paths[keep:]:
        path.unlink(missing_ok=True)
```

- [ ] **Step 4: Verificar**

Run: `python -m pytest app/tests/test_backups.py -v`
Expected: PASS.

- [ ] **Step 5: Stage + confirmación de commit**

```bash
git add backend/app/modules/security/service.py backend/app/tests/test_backups.py
```
Mensaje: `feat(security): rotación de backups (retiene los 20 últimos)`

---

## FASE 3 — Rendimiento

### Task 7: Paginación en /api/transactions + dashboard con limit=5

**Files:**
- Modify: `backend/app/modules/transactions/routes.py:29-52`
- Modify: `apps/desktop/src/lib/api/transactions.ts:16-25`
- Modify: `apps/desktop/src/features/dashboard/DashboardPage.tsx:30,38`
- Test: `backend/app/tests/` (junto a los tests de transactions existentes; buscar con grep `def test_.*transaction` para ubicar el fichero)

- [ ] **Step 1: Test que falla**

```python
def test_list_transactions_respects_limit_and_offset(client):
    acc = client.post("/api/accounts", json={"name": "Test", "type": "checking", "currency": "EUR"}).json()
    for i in range(5):
        client.post("/api/transactions", json={
            "account_id": acc["id"], "date": f"2026-03-0{i+1}",
            "description": f"tx{i}", "amount": "-1.00", "type": "expense",
        })
    assert len(client.get("/api/transactions?limit=2").json()) == 2
    page2 = client.get("/api/transactions?limit=2&offset=2").json()
    assert len(page2) == 2
    assert page2[0]["description"] != client.get("/api/transactions?limit=2").json()[0]["description"]
```

Nota: verificar el payload real de creación de cuenta contra `accounts/schemas.py` antes de ejecutar (campos exactos).

- [ ] **Step 2: Verificar que falla**

Run: `python -m pytest app/tests/ -k limit_and_offset -v`
Expected: FAIL (limit ignorado → 5 filas).

- [ ] **Step 3: Implementación backend**

En `list_transactions`, añadir parámetros y aplicarlos al final:

```python
def list_transactions(
    account_id: str | None = Query(None),
    category_id: str | None = Query(None),
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    type: str | None = Query(None),
    source: str | None = Query(None),
    limit: int | None = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[Transaction]:
    ...
    q = q.order_by(Transaction.date.desc())
    if offset:
        q = q.offset(offset)
    if limit is not None:
        q = q.limit(limit)
    return _stamp_account_names(db, q.all())
```

Sin `limit` la respuesta es completa — retrocompatible con todas las páginas existentes.

- [ ] **Step 4: Verificar backend**

Run: `python -m pytest app/tests/ -k transaction -v`
Expected: PASS.

- [ ] **Step 5: Frontend**

En `transactions.ts`, ampliar filtros:

```typescript
export interface TransactionFilters {
  account_id?: string;
  category_id?: string;
  from_date?: string;
  to_date?: string;
  type?: string;
  limit?: number;
  offset?: number;
}
```

En `DashboardPage.tsx`, línea 30:

```typescript
  const { transactions } = useTransactions({ limit: 5 });
```

y línea 38 pasa a `const recent = transactions;` (ya vienen 5).

- [ ] **Step 6: Verificar frontend**

Run (desde `apps/desktop`): `npx tsc --noEmit`
Expected: sin errores.

- [ ] **Step 7: Stage + confirmación de commit**

```bash
git add backend/app/modules/transactions/routes.py backend/app/tests/ apps/desktop/src/lib/api/transactions.ts apps/desktop/src/features/dashboard/DashboardPage.tsx
```
Mensaje: `perf(transactions): paginación limit/offset; el dashboard pide solo 5 movimientos`

---

### Task 8: Eliminar N+1 en preview y confirm de importación

Preview: un query de duplicado **por fila**. Confirm: un query de contrapartida **por transacción**. Con 1.000 filas ≈ 2.000 queries.

**Files:**
- Modify: `backend/app/modules/imports/routes.py` (preview ~83-88, confirm ~255-282)
- Test: los tests existentes de `test_imports.py` cubren el comportamiento; esta tarea no lo cambia.

- [ ] **Step 1: Preview — dedupe con un solo IN**

Reestructurar el bucle del preview en dos pasadas: primera pasada normaliza todas las filas (con el contador de ocurrencias de la Task 2) acumulando `(number, raw, normalized, errors, warnings, skipped_reason)`; después un único query:

```python
    all_hashes = [n["duplicate_hash"] for _, _, n, _, _, _ in processed]
    existing_hashes: set[str] = set()
    for chunk_start in range(0, len(all_hashes), 500):  # límite de variables de SQLite
        chunk = all_hashes[chunk_start : chunk_start + 500]
        existing_hashes.update(
            h for (h,) in db.query(Transaction.external_id).filter(Transaction.external_id.in_(chunk))
        )
```

y la segunda pasada clasifica cada fila con `duplicate = normalized["duplicate_hash"] in existing_hashes` y crea los `ImportRow` exactamente como hoy. El resultado del endpoint no cambia.

- [ ] **Step 2: Confirm — contrapartidas con un solo query**

Sustituir el query-por-transacción del emparejado por una precarga:

```python
    if new_txs:
        dates = [date_cls.fromisoformat(t.date) for t in new_txs]
        lo = (min(dates) - timedelta(days=3)).isoformat()
        hi = (max(dates) + timedelta(days=3)).isoformat()
        amounts = {-t.amount for t in new_txs}
        candidates = (
            db.query(Transaction)
            .filter(
                Transaction.amount.in_(list(amounts)),
                Transaction.type.in_(["income", "expense"]),
                Transaction.date >= lo,
                Transaction.date <= hi,
            )
            .all()
        )
    else:
        candidates = []
```

y el bucle empareja en Python (misma semántica que el filtro SQL actual + el indicio de la Task 4):

```python
    for tx in new_txs:
        if tx.type not in ("income", "expense") or tx.id in used_ids:
            continue
        tx_date = date_cls.fromisoformat(tx.date)
        counterpart = next(
            (
                c for c in candidates
                if c.id != tx.id
                and c.id not in used_ids
                and c.account_id != tx.account_id
                and c.amount == -tx.amount
                and c.currency == tx.currency
                and c.type in ("income", "expense")
                and abs((date_cls.fromisoformat(c.date) - tx_date).days) <= 3
                and (_looks_like_transfer(tx.description) or _looks_like_transfer(c.description))
            ),
            None,
        )
        if counterpart is not None:
            ...  # cuerpo idéntico al actual
```

- [ ] **Step 3: Verificar que nada cambia funcionalmente**

Run: `python -m pytest app/tests/test_imports.py app/tests/test_reconciliation.py -v`
Expected: PASS todos (misma semántica, menos queries).

- [ ] **Step 4: Stage + confirmación de commit**

```bash
git add backend/app/modules/imports/routes.py
```
Mensaje: `perf(imports): dedupe y emparejado de traspasos en queries batch (elimina N+1)`

---

### Task 9: Refresh de precios en paralelo

**Files:**
- Modify: `backend/app/modules/investments/price_service.py:47-138`
- Test: `backend/app/tests/test_investments.py` (los existentes; el paralelismo no cambia el contrato)

- [ ] **Step 1: Implementación**

En `refresh_prices`, tras cargar `holdings` y sus assets, prefetch paralelo de precios (solo red; la sesión de BD no se toca desde los hilos):

```python
from concurrent.futures import ThreadPoolExecutor
```

```python
        assets_by_holding: dict[str, InvestmentAsset] = {}
        for h in holdings:
            asset = db.query(InvestmentAsset).filter(InvestmentAsset.id == h.asset_id).first()
            if asset:
                assets_by_holding[h.id] = asset

        tickers = {
            a.ticker
            for a in assets_by_holding.values()
            if a.ticker and (a.asset_type or "unknown") not in {"cash", "savings_account"}
        }
        # ponytail: hasta 8 hilos solo para el fetch HTTP; la BD se escribe en serie después.
        prices: dict[str, Decimal | None] = {}
        if tickers:
            with ThreadPoolExecutor(max_workers=8) as pool:
                for ticker, price in zip(tickers, pool.map(cls.fetch_ticker_price, tickers)):
                    prices[ticker] = price
```

y en el bucle principal sustituir `price = cls.fetch_ticker_price(asset.ticker)` por `price = prices.get(asset.ticker)`. El camino de reintento con `resolve_asset` (líneas 92-101) se queda como está — es el caso raro y secuencial está bien.

También cargar los assets desde `assets_by_holding` en el bucle en lugar del query por holding (aprovechar el dict ya construido).

- [ ] **Step 2: Verificar**

Run: `python -m pytest app/tests/test_investments.py app/tests/test_asset_resolution_flow.py -v`
Expected: PASS (los tests mockean `fetch_ticker_price`, que sigue siendo el único punto de red).

- [ ] **Step 3: Stage + confirmación de commit**

```bash
git add backend/app/modules/investments/price_service.py
```
Mensaje: `perf(investments): fetch de precios en paralelo (8 hilos)`

---

### Task 10: Caché TTL de GETs en el cliente API

Navegar entre páginas hoy relanza todas las llamadas. Caché en memoria de 30 s para GETs, invalidada por completo en cualquier mutación.

**Files:**
- Modify: `apps/desktop/src/lib/api/client.ts`

- [ ] **Step 1: Implementación**

En `client.ts` (integrando con los cambios de la Task 5):

```typescript
// Caché de GETs: evita repetir las mismas llamadas al navegar entre páginas.
// ponytail: TTL fijo de 30 s e invalidación total en cualquier mutación;
// si hace falta invalidación por recurso o revalidación en segundo plano, migrar a TanStack Query.
const CACHE_TTL_MS = 30_000;
const getCache = new Map<string, { at: number; promise: Promise<unknown> }>();

function cachedGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  const hit = getCache.get(path);
  if (hit && Date.now() - hit.at < CACHE_TTL_MS) {
    return hit.promise as Promise<T>;
  }
  const promise = request<T>(path, undefined, signal);
  getCache.set(path, { at: Date.now(), promise });
  promise.catch(() => getCache.delete(path)); // no cachear errores
  return promise;
}

function invalidateCache(): void {
  getCache.clear();
}

export const api = {
  get: <T>(path: string, signal?: AbortSignal) => cachedGet<T>(path, signal),
  post: <T>(path: string, body: unknown, signal?: AbortSignal) => {
    invalidateCache();
    return request<T>(path, { method: "POST", body: JSON.stringify(body) }, signal);
  },
  upload: <T>(path: string, body: FormData) => {
    invalidateCache();
    return request<T>(path, { method: "POST", body });
  },
  put: <T>(path: string, body: unknown) => {
    invalidateCache();
    return request<T>(path, { method: "PUT", body: JSON.stringify(body) });
  },
  patch: <T>(path: string, body: unknown) => {
    invalidateCache();
    return request<T>(path, { method: "PATCH", body: JSON.stringify(body) });
  },
  delete: <T>(path: string) => {
    invalidateCache();
    return request<T>(path, { method: "DELETE" });
  },
};
```

Cuidado con `signal`: si un componente aborta el fetch compartido, los demás consumidores del mismo path recibirían el abort. Mitigación simple: **no pasar el signal al fetch cacheado** — eliminar el parámetro `signal` de `cachedGet` y llamar `request<T>(path)` (los GETs son idempotentes y de 30 s de vida; abortarlos no aporta). Mantener la firma pública `api.get(path, signal?)` para no romper llamadas existentes, ignorando el signal con un comentario.

Excepción: los endpoints de "reload" explícito (botón refrescar) esperan datos frescos. `reload()` de los hooks vuelve a llamar `api.get` y recibiría el caché. Añadir un escape:

```typescript
  getFresh: <T>(path: string) => {
    getCache.delete(path);
    return cachedGet<T>(path);
  },
```

y NO cambiar los hooks en esta tarea: 30 s de TTL hace que el reload manual casi siempre siga siendo correcto; usar `getFresh` solo donde alguien lo pida.

- [ ] **Step 2: Verificar**

Run (desde `apps/desktop`): `npx tsc --noEmit`
Expected: sin errores.
Verificación manual (con backend en dev): navegar Dashboard → Finanzas → Dashboard con la pestaña Network del devtools abierta; la segunda visita al Dashboard no debe relanzar `/api/transactions` ni `/api/dashboard/overview` dentro de los 30 s. Tras crear una transacción, sí debe refrescar.

- [ ] **Step 3: Stage + confirmación de commit**

```bash
git add apps/desktop/src/lib/api/client.ts
```
Mensaje: `perf(frontend): caché TTL de 30s para GETs con invalidación en mutaciones`

---

## FASE 4 — Exactitud de datos de mercado

### Task 11: FX sin fallback silencioso a 1.0

**Files:**
- Modify: `backend/app/modules/investments/price_service.py:30-44,116-124`
- Test: `backend/app/tests/test_investments.py`

- [ ] **Step 1: Test que falla**

Añadir a `test_investments.py` (adaptar al estilo de mock existente del fichero — buscar cómo mockean `fetch_ticker_price` y seguir el mismo patrón):

```python
def test_fx_failure_marks_holding_manual_instead_of_rate_1(client, monkeypatch):
    from app.modules.investments.price_service import PriceService

    def fake_fetch(ticker: str):
        if ticker.startswith("EUR"):  # FX caído
            return None
        return Decimal("100")

    monkeypatch.setattr(PriceService, "fetch_ticker_price", staticmethod(fake_fetch))
    # crear asset USD + holding vía API como hacen los tests existentes...
    # tras refresh: el holding en USD NO debe tener market_value calculado con tipo 1.0
    # y debe aparecer en manual_required con reason "fx_unavailable".
```

Completar la creación de asset/holding copiando el fixture del test de refresh existente en el mismo fichero (hay tests de `refresh_prices`; reutilizar su setup). El assert clave:

```python
    assert any(item["reason"] == "fx_unavailable" for item in result["manual_required"])
```

- [ ] **Step 2: Verificar que falla**

Run: `python -m pytest app/tests/test_investments.py -k fx_failure -v`
Expected: FAIL (hoy `market_value` se calcula con rate 1.0 y no hay `fx_unavailable`).

- [ ] **Step 3: Implementación**

En `price_service.py`:

```python
    @classmethod
    def get_eur_rate(cls, currency: str, cache: dict[str, Decimal | None]) -> Decimal | None:
        """Unidades de `currency` por 1 EUR; None si el tipo no está disponible."""
        currency = (currency or "EUR").upper()
        if currency == "EUR":
            return Decimal("1.0")
        if currency not in cache:
            cache[currency] = cls.fetch_ticker_price(f"EUR{currency}=X")
        return cache[currency]
```

(eliminar `get_eur_usd_rate` si no tiene más llamadores — verificar con grep `get_eur_usd_rate` antes; si tiene llamadores, actualizarlos igual)

En `refresh_prices`, tras obtener el precio:

```python
            rate = cls.get_eur_rate(asset.currency, fx_cache)
            if rate is None:
                # Sin tipo de cambio no hay valor fiable: mejor pedir intervención
                # que valorar con un tipo inventado.
                result.manual_required.append({
                    "holding_id": h.id,
                    "name": asset.name,
                    "symbol": asset.ticker,
                    "asset_type": asset_type,
                    "reason": "fx_unavailable",
                })
                result.needs_manual_nav.append(h.id)
                continue
            if asset.price_source == "manual":
                asset.price_source = "yfinance"
            h.current_price = price
            h.current_price_currency = asset.currency
            h.current_price_updated_at = datetime.now(timezone.utc)
            h.market_value = (h.quantity * price / rate).quantize(Decimal("0.01"))
```

(el `continue` va **antes** de escribir `h.current_price`, para no dejar el holding a medio actualizar)

- [ ] **Step 4: Verificar**

Run: `python -m pytest app/tests/test_investments.py -v`
Expected: PASS.

- [ ] **Step 5: Stage + confirmación de commit**

```bash
git add backend/app/modules/investments/price_service.py backend/app/tests/test_investments.py
```
Mensaje: `fix(investments): FX no disponible marca la posición en vez de valorar con tipo 1.0`

---

### Task 12: Logging de fallos en fetch_ticker_price

**Files:**
- Modify: `backend/app/modules/investments/price_service.py:22-28`

- [ ] **Step 1: Implementación**

```python
import logging

logger = logging.getLogger("investments.prices")
```

```python
    @staticmethod
    def fetch_ticker_price(ticker: str) -> Decimal | None:
        try:
            price = yf.Ticker(ticker).fast_info.last_price
            return Decimal(str(price)) if price is not None else None
        except Exception as exc:  # noqa: BLE001 — el llamador decide; aquí solo se registra
            logger.warning("fetch de %s falló: %s", ticker, exc)
            return None
```

- [ ] **Step 2: Verificar**

Run: `python -m pytest app/tests/test_investments.py -v`
Expected: PASS (sin cambio de contrato).

- [ ] **Step 3: Stage + confirmación de commit** (puede ir junto al commit de la Task 11 si se ejecutan seguidas)

```bash
git add backend/app/modules/investments/price_service.py
```
Mensaje: `chore(investments): log de fallos de yfinance para diagnóstico`

---

### Task 13: Re-ingesta periódica + "última actualización" en Economía

La ingesta de indicadores macro corre solo al arrancar; con la app abierta días, los datos se congelan sin aviso.

**Files:**
- Modify: `backend/app/modules/market_intelligence/ingestion/startup.py`
- Modify: `apps/desktop/src/features/economy/EconomyPage.tsx`
- Test: `backend/app/tests/test_economy_data_integrity.py` (los existentes; el loop no se testea, la función de un ciclo sí queda cubierta por los tests actuales de ingest)

- [ ] **Step 1: Backend — loop periódico**

En `startup.py`, transformar el daemon thread en un bucle. Extraer el cuerpo actual de `_run` a `_run_once()` (idéntico, incluida la purga y la actualización de `_status`) y:

```python
import time

REINGEST_INTERVAL_SECONDS = 6 * 3600  # ponytail: intervalo fijo; configurable si algún proveedor lo pide


def launch_startup_ingest() -> None:
    """Ingesta al arrancar y re-ingesta cada 6 h mientras la app viva."""
    def _loop() -> None:
        while True:
            _run_once()
            time.sleep(REINGEST_INTERVAL_SECONDS)

    Thread(target=_loop, daemon=True).start()
```

`_run_once()` ya deja `_status["last_run"]` con el timestamp — es lo que consume el frontend.

- [ ] **Step 2: Verificar backend**

Run: `python -m pytest app/tests/test_economy_data_integrity.py -v`
Expected: PASS. Si algún test llama a `launch_startup_ingest` directamente y ahora quedaría en bucle, apuntar el test a `_run_once` (el loop es composición trivial).

- [ ] **Step 3: Frontend — mostrar frescura**

`EconomyPage.tsx` ya recibe `ingestStatus` de `useEconomyMI()` (línea 78). Añadir bajo el `PageHeader` (localizar el `<PageHeader` del render principal):

```tsx
      {ingestStatus?.last_run && (
        <p className="text-caption text-stone">
          Datos actualizados: {new Date(ingestStatus.last_run).toLocaleString("es-ES", {
            day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
          })}
        </p>
      )}
      {ingestStatus?.storage === "memory" && (
        <div className="rounded-lg border border-accent-warning/40 bg-accent-warning/10 p-3">
          <p className="text-body-sm text-accent-warning">{ingestStatus.storage_warning}</p>
        </div>
      )}
```

Verificar en `apps/desktop/src/lib/types/market-intelligence.ts` que `IngestStatus` incluye `last_run`, `storage` y `storage_warning`; si faltan, añadirlos como opcionales:

```typescript
  last_run?: string | null;
  storage?: "memory" | "file";
  storage_warning?: string;
```

- [ ] **Step 4: Verificar frontend**

Run (desde `apps/desktop`): `npx tsc --noEmit` → sin errores.
Después: `npm run ux:snapshots:headed` y revisar la captura de Economía.

- [ ] **Step 5: Stage + confirmación de commit**

```bash
git add backend/app/modules/market_intelligence/ingestion/startup.py apps/desktop/src/features/economy/EconomyPage.tsx apps/desktop/src/lib/types/market-intelligence.ts
```
Mensaje: `feat(economy): re-ingesta cada 6h y frescura visible en la página de Economía`

---

## FASE 5 — Flujo de importación

### Task 14: Aviso "archivo ya importado" + purga de previews huérfanos

**Files:**
- Modify: `backend/app/modules/imports/routes.py` (preview)
- Modify: `backend/app/main.py` (purga en lifespan)
- Test: `backend/app/tests/test_imports.py`

- [ ] **Step 1: Test que falla**

```python
def test_preview_warns_when_file_already_imported(client):
    csv = "date,amount,description\n01/03/2026,-10.00,Mercadona\n"
    files = {"file": ("compra.csv", csv.encode(), "text/csv")}
    first = client.post("/api/imports/preview", files=files).json()
    client.post(f"/api/imports/{first['import_batch_id']}/confirm", json={})

    second = client.post("/api/imports/preview", files=files).json()
    assert second["already_imported_at"] is not None

    fresh = client.post(
        "/api/imports/preview",
        files={"file": ("otro.csv", csv.replace("Mercadona", "Lidl").encode(), "text/csv")},
    ).json()
    assert fresh["already_imported_at"] is None
```

- [ ] **Step 2: Verificar que falla**

Run: `python -m pytest app/tests/test_imports.py -k already_imported -v`
Expected: FAIL (`KeyError: already_imported_at`).

- [ ] **Step 3: Implementación**

En el endpoint `preview`, tras calcular el hash del archivo:

```python
    file_hash = hashlib.sha256(content).hexdigest()
    previous = (
        db.query(ImportBatch)
        .filter(ImportBatch.file_hash == file_hash, ImportBatch.status == "imported")
        .order_by(ImportBatch.created_at.desc())
        .first()
    )
```

y en el dict de respuesta:

```python
        "already_imported_at": previous.completed_at.isoformat() if previous and previous.completed_at else None,
```

Purga de huérfanos — en `main.py`, dentro de `lifespan` tras los seeds:

```python
    # Previews abandonados: batches 'validated' de hace más de 7 días y sus filas.
    from datetime import datetime, timedelta, timezone

    from app.models.import_batch import ImportBatch, ImportRow

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    stale_ids = [
        b.id
        for b in db.query(ImportBatch).filter(
            ImportBatch.status == "validated", ImportBatch.created_at < cutoff
        )
    ]
    if stale_ids:
        db.query(ImportRow).filter(ImportRow.import_batch_id.in_(stale_ids)).delete()
        db.query(ImportBatch).filter(ImportBatch.id.in_(stale_ids)).delete()
        db.commit()
```

(colocarlo dentro del `try` existente que ya cierra `db` en `finally`)

- [ ] **Step 4: Frontend — mostrar el aviso**

En la página de importación (`apps/desktop/src/features/imports/ImportsPage.tsx` o `features/finances` según dónde viva el preview — localizar con grep `preview_rows`), donde se renderiza el resumen del preview, añadir:

```tsx
      {preview.already_imported_at && (
        <div className="rounded-lg border border-accent-warning/40 bg-accent-warning/10 p-3">
          <p className="text-body-sm text-accent-warning">
            Este archivo ya se importó el {new Date(preview.already_imported_at).toLocaleDateString("es-ES")}.
            Si continúas, los movimientos ya existentes se marcarán como duplicados.
          </p>
        </div>
      )}
```

y añadir `already_imported_at: string | null` al tipo del preview en `apps/desktop/src/lib/api/imports.ts`.

- [ ] **Step 5: Verificar**

Run: `python -m pytest app/tests/test_imports.py -v` → PASS.
Run (desde `apps/desktop`): `npx tsc --noEmit` → sin errores.

- [ ] **Step 6: Stage + confirmación de commit**

```bash
git add backend/app/modules/imports/routes.py backend/app/main.py backend/app/tests/test_imports.py apps/desktop/src/lib/api/imports.ts apps/desktop/src/features/imports/ apps/desktop/src/features/finances/
```
Mensaje: `feat(imports): aviso de archivo ya importado y purga de previews huérfanos`

---

### Task 15: Aprendizaje de categorías por comercio

Cada corrección manual de categoría se convierte en regla permanente: tabla `merchant_rules` (descripción normalizada → categoría). En importación, la regla exacta gana al diccionario de keywords.

**Files:**
- Create: `backend/app/models/merchant_rule.py`
- Modify: `backend/app/models/__init__.py` (registrar el modelo — seguir el patrón de imports existente del fichero)
- Modify: `backend/app/modules/transactions/routes.py` (PATCH aprende)
- Modify: `backend/app/modules/imports/routes.py` (lookup en preview y confirm)
- Test: `backend/app/tests/test_imports.py`

**Interfaces:**
- Produces: `MerchantRule(merchant: str [normalizado, unique], category_id: str)`; helper `learned_category(db, description) -> str | None` en `auto_categorizer.py` que devuelve el **nombre** de la categoría.

- [ ] **Step 1: Test que falla**

```python
def test_manual_recategorization_teaches_importer(client):
    csv = "date,amount,description\n01/03/2026,-25.00,GIMNASIO MISTERIOSO SL\n"
    first = _import_csv(client, "gym1.csv", csv)  # helper de la Task 4
    txs = client.get("/api/transactions?source=csv").json()
    tx = next(t for t in txs if "MISTERIOSO" in t["description"])
    assert tx["category_id"] is None  # ninguna keyword lo conoce

    deportes = next(c for c in client.get("/api/categories").json() if c["name"] == "Deportes")
    client.patch(f"/api/transactions/{tx['id']}", json={"category_id": deportes["id"]})

    # Mismo comercio en un archivo nuevo (fecha distinta para no ser duplicado)
    csv2 = "date,amount,description\n05/04/2026,-25.00,GIMNASIO MISTERIOSO SL\n"
    _import_csv(client, "gym2.csv", csv2)
    txs = client.get("/api/transactions?source=csv").json()
    learned = [t for t in txs if "MISTERIOSO" in t["description"]]
    assert any(t["category_id"] == deportes["id"] for t in learned if t["date"] == "2026-04-05")
```

Nota: verificar la forma real de la respuesta de `/api/categories` (lista plana vs anidada) antes de ejecutar.

- [ ] **Step 2: Verificar que falla**

Run: `python -m pytest app/tests/test_imports.py -k teaches -v`
Expected: FAIL en el último assert.

- [ ] **Step 3: Modelo**

Crear `backend/app/models/merchant_rule.py`:

```python
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MerchantRule(Base):
    """Regla aprendida de una corrección manual: comercio → categoría.

    ponytail: match por descripción normalizada exacta; si los bancos añaden
    sufijos variables (nº de operación), pasar a match por prefijo de tokens.
    """

    __tablename__ = "merchant_rules"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    category_id: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
```

Registrarlo en `backend/app/models/__init__.py` siguiendo el patrón del fichero. `create_tables()` crea la tabla nueva automáticamente (es tabla nueva, no ALTER — no necesita `_migrate_*`).

- [ ] **Step 4: Aprender en el PATCH**

En `transactions/routes.py`, en `update_transaction`, tras aplicar los campos y antes del `db.commit()`:

```python
    if payload.category_id is not None and tx.description:
        from app.models.merchant_rule import MerchantRule
        from app.modules.imports.auto_categorizer import _normalize

        merchant = _normalize(tx.description)
        rule = db.query(MerchantRule).filter(MerchantRule.merchant == merchant).first()
        if rule:
            rule.category_id = payload.category_id
        else:
            db.add(MerchantRule(merchant=merchant, category_id=payload.category_id))
```

- [ ] **Step 5: Consultar en importación**

En `auto_categorizer.py`, añadir:

```python
def learned_category(db, description: str) -> str | None:
    """Nombre de categoría aprendida de correcciones manuales, o None."""
    from app.models.category import Category
    from app.models.merchant_rule import MerchantRule

    rule = db.query(MerchantRule).filter(MerchantRule.merchant == _normalize(description)).first()
    if rule is None:
        return None
    category = db.query(Category).filter(Category.id == rule.category_id).first()
    return category.name if category else None
```

En `imports/routes.py`, en los dos puntos donde se infiere categoría (preview ~línea 77 y confirm ~línea 185), anteponer la regla aprendida:

```python
        if not normalized["category"] and normalized["type"] != "transfer":
            normalized["category"] = (
                learned_category(db, normalized["description"])
                or auto_category(normalized["description"])
                or ""
            )
```

(actualizar el import: `from app.modules.imports.auto_categorizer import auto_category, learned_category`)

- [ ] **Step 6: Verificar**

Run: `python -m pytest app/tests/test_imports.py -v`
Expected: PASS todos.

- [ ] **Step 7: Stage + confirmación de commit**

```bash
git add backend/app/models/merchant_rule.py backend/app/models/__init__.py backend/app/modules/transactions/routes.py backend/app/modules/imports/auto_categorizer.py backend/app/modules/imports/routes.py backend/app/tests/test_imports.py
```
Mensaje: `feat(imports): las correcciones manuales de categoría enseñan al importador`

---

## FASE 6 — UI

### Task 16: Copy en español + skeletons por sección en Dashboard

**Files:**
- Modify: `apps/desktop/src/features/dashboard/DashboardPage.tsx`
- Verificar: grep de otros textos en inglés en `apps/desktop/src/features/` y `src/app/`

- [ ] **Step 1: Copy**

En `DashboardPage.tsx` línea 44: `eyebrow="Private command center"` → `eyebrow="Centro de control privado"`.

Buscar más textos en inglés visibles: `grep -rn "command center\|Powered by\|Overview\|Insights\b" apps/desktop/src/features apps/desktop/src/app --include=*.tsx` y traducir los que sean copy de UI (no identificadores). Solo copy visible; nombres de rutas/props no se tocan.

- [ ] **Step 2: Skeletons por sección**

Hoy `if (loading) return <LoadingState .../>` bloquea toda la página hasta que llega `overview`, y el resto de widgets hace pop-in. Cambio mínimo coherente: mantener el gate global SOLO para overview, y dar placeholder estable a las secciones que dependen de otros hooks. En `DashboardPage.tsx`:

```tsx
function CardSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="animate-pulse space-y-2 py-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-4 rounded bg-surface-elevated" />
      ))}
    </div>
  );
}
```

y en cada `SectionCard`, usar el estado de carga de su hook (los hooks ya devuelven `loading`):

```tsx
  const { transactions, loading: txLoading } = useTransactions({ limit: 5 });
  ...
  <SectionCard title="Últimos movimientos" more="/finances?tab=movimientos">
    {txLoading ? <CardSkeleton rows={5} /> : recent.length === 0 ? ( ... ) : ( ... )}
  </SectionCard>
```

Aplicar el mismo patrón a las secciones de portafolio (`useHoldings`/`useInvestmentSummary` — comprobar el nombre real del flag de loading que exponen esos hooks), objetivos e insights.

- [ ] **Step 3: Verificar**

Run (desde `apps/desktop`): `npx tsc --noEmit` → sin errores.
Run: `npm run ux:snapshots:headed` → revisar Dashboard en las capturas.

- [ ] **Step 4: Stage + confirmación de commit**

```bash
git add apps/desktop/src/features/ apps/desktop/src/app/
```
Mensaje: `ui(dashboard): copy 100% en español y skeletons por sección`

---

## Verificación final (tras la última tarea)

- [ ] Backend completo: `python -m pytest app/tests/ -v` — todos PASS (autorizado por este plan).
- [ ] Frontend: `npx tsc --noEmit` sin errores.
- [ ] UX: `npm run ux:snapshots:headed` y revisión visual de Dashboard, Economía e Importación.
- [ ] Presentar al usuario el resumen de commits staged pendientes de confirmación.
