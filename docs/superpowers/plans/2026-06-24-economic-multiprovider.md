# Economic Intelligence Multi-Provider — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ampliar economic intelligence con tres nuevos providers (ECB, OECD, World Bank) y un `EconomicProviderRouter` con lógica de autoridad por fuente, cross-validation y `confidence_score` por indicador.

**Architecture:** Cada indicador tiene una fuente primaria autoritativa (ECB para EA, FRED para US) y validadores opcionales. El `EconomicProviderRouter` llama al primario, lanza validadores en paralelo, calcula `confidence_score` (0.7–1.0) y devuelve el valor primario con metadatos de confianza. Si el primario falla, el primer validador disponible asciende. La capa de servicio delega en el router en lugar de llamar directamente a FRED y Stooq.

**Tech Stack:** Python 3.11, FastAPI, DuckDB (cache), `requests`, `concurrent.futures`, PyYAML. React 18, TypeScript, Tailwind CSS.

## Global Constraints

- Ningún provider de pago. ECB, OECD y World Bank son gratuitos sin API key.
- FRED_API_KEY sigue siendo opcional — si no está configurada, FRED falla en abierto y el router usa validadores como primario.
- UI en español. Dark Premium theme. No añadir dependencias nuevas.
- Todos los tests con `pytest`. Correr desde `backend/`: `python -m pytest app/tests/ -v`.
- El LLM no llama a estos providers directamente — solo consume los endpoints `/api/economy/*`.

---

## File Map

| Acción | Archivo |
|--------|---------|
| CREAR | `backend/app/modules/economic_data/providers/ecb_provider.py` |
| CREAR | `backend/app/modules/economic_data/providers/oecd_provider.py` |
| CREAR | `backend/app/modules/economic_data/providers/worldbank_provider.py` |
| CREAR | `backend/app/modules/economic_data/economic_data_config.yaml` |
| CREAR | `backend/app/modules/economic_data/provider_router.py` |
| MODIFICAR | `backend/app/modules/economic_data/schemas.py` |
| MODIFICAR | `backend/app/modules/economic_data/repository.py` |
| MODIFICAR | `backend/app/modules/economic_data/service.py` |
| CREAR | `backend/app/tests/test_ecb_provider.py` |
| CREAR | `backend/app/tests/test_oecd_provider.py` |
| CREAR | `backend/app/tests/test_worldbank_provider.py` |
| CREAR | `backend/app/tests/test_economic_router.py` |
| MODIFICAR | `apps/desktop/src/lib/types/index.ts` |
| MODIFICAR | `apps/desktop/src/features/economy/components/IndicatorCard.tsx` |

---

### Task 1: `EcbProvider`

**Files:**
- Create: `backend/app/modules/economic_data/providers/ecb_provider.py`
- Create: `backend/app/tests/test_ecb_provider.py`

**Interfaces:**
- Produces: `EcbProvider.fetch_series(series_key: str) -> Optional[dict]` y `EcbProvider.fetch_all() -> list[dict]`
- `dict` devuelto tiene las mismas claves que `FredProvider`: `series_id`, `region`, `indicator`, `name`, `unit`, `source`, `value`, `prev_value`, `observation_date`, `period`.

- [ ] **Step 1: Escribir los tests**

Crear `backend/app/tests/test_ecb_provider.py`:

```python
from unittest.mock import MagicMock, patch
import pytest


def _make_ecb_json(value: str, prev_value: str = "3.5") -> dict:
    """Minimal ECB SDMX-JSON response with two observations."""
    return {
        "dataSets": [{
            "series": {
                "0:0:0:0:0:0:0": {
                    "observations": {
                        "0": [float(prev_value)],
                        "1": [float(value)],
                    }
                }
            }
        }],
        "structure": {
            "dimensions": {
                "observation": [{"values": [
                    {"id": "2026-04"},
                    {"id": "2026-05"},
                ]}]
            }
        }
    }


def test_fetch_series_parses_value_and_prev():
    from app.modules.economic_data.providers.ecb_provider import EcbProvider
    provider = EcbProvider()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = _make_ecb_json("2.4", "2.6")

    with patch("app.modules.economic_data.providers.ecb_provider.requests.get", return_value=mock_resp):
        result = provider.fetch_series("ICP/M.U2.N.000000.4.ANR", "EA", "inflation", "Inflación EA", "%")

    assert result is not None
    assert result["value"] == 2.4
    assert result["prev_value"] == 2.6
    assert result["source"] == "ECB"


def test_fetch_series_returns_none_on_empty_dataset():
    from app.modules.economic_data.providers.ecb_provider import EcbProvider
    provider = EcbProvider()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"dataSets": [{"series": {}}], "structure": {"dimensions": {"observation": [{"values": []}]}}}

    with patch("app.modules.economic_data.providers.ecb_provider.requests.get", return_value=mock_resp):
        result = provider.fetch_series("ICP/M.U2.N.000000.4.ANR", "EA", "inflation", "Inflación EA", "%")

    assert result is None


def test_fetch_series_returns_none_on_http_error():
    from app.modules.economic_data.providers.ecb_provider import EcbProvider
    provider = EcbProvider()

    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.raise_for_status.side_effect = Exception("404")

    with patch("app.modules.economic_data.providers.ecb_provider.requests.get", return_value=mock_resp):
        result = provider.fetch_series("BAD/KEY", "EA", "inflation", "Test", "%")

    assert result is None


def test_fetch_series_returns_none_on_timeout():
    from app.modules.economic_data.providers.ecb_provider import EcbProvider
    import requests as req
    provider = EcbProvider()

    with patch("app.modules.economic_data.providers.ecb_provider.requests.get", side_effect=req.Timeout):
        result = provider.fetch_series("ICP/M.U2.N.000000.4.ANR", "EA", "inflation", "Test", "%")

    assert result is None


def test_fetch_all_returns_list_of_dicts():
    from app.modules.economic_data.providers.ecb_provider import EcbProvider
    provider = EcbProvider()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = _make_ecb_json("2.4")

    with patch("app.modules.economic_data.providers.ecb_provider.requests.get", return_value=mock_resp):
        results = provider.fetch_all()

    assert isinstance(results, list)
    assert len(results) > 0
    assert all("series_id" in r and "value" in r for r in results)
```

- [ ] **Step 2: Verificar que fallan**

```
cd backend
python -m pytest app/tests/test_ecb_provider.py -v
```

Esperado: `ImportError` (módulo no existe).

- [ ] **Step 3: Implementar `EcbProvider`**

Crear `backend/app/modules/economic_data/providers/ecb_provider.py`:

```python
"""ECB Data Warehouse provider (SDMX-JSON, no API key required).

API base: https://data-api.ecb.europa.eu/service/data/{flow}/{key}
Format: ?format=jsondata&lastNObservations=2
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_BASE_URL = "https://data-api.ecb.europa.eu/service/data"
_TIMEOUT = 12

# (series_key, region, indicator, name, unit)
# ⚠️ Verificar series keys exactas en https://data-api.ecb.europa.eu durante implementación.
ECB_SERIES: list[tuple[str, str, str, str, str]] = [
    ("ICP/M.U2.N.000000.4.ANR", "EA", "inflation",    "Inflación Eurozona HICP",    "%"),
    ("ICP/M.ES.N.000000.4.ANR", "ES", "inflation",    "Inflación España HICP",      "%"),
    ("FM/B.U2.EUR.RT.MM.EURIBOR3MD_.HSTA",  "EA", "euribor", "Euríbor 3M",  "%"),
    ("FM/B.U2.EUR.RT.MM.EURIBOR1YD_.HSTA",  "EA", "euribor", "Euríbor 12M", "%"),
    ("FM/B.U2.EUR.RF.IN.T.EUR.FDFR.ST",    "EA", "policy_rate", "Tipo depósito BCE", "%"),
    ("BP6/M.U2.W1.S1.S1.T.B.CA._Z.EUR.T.M", "EA", "current_account", "Balanza c/c Eurozona", "M€"),
]

_MONTHS_ES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
              "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _format_period(period_id: str) -> str:
    """Convert '2026-05' → 'mayo 2026'."""
    try:
        if len(period_id) == 7:  # YYYY-MM
            year, month = int(period_id[:4]), int(period_id[5:7])
            return f"{_MONTHS_ES[month]} {year}"
    except (ValueError, IndexError):
        pass
    return period_id


class EcbProvider:
    def fetch_series(
        self,
        series_key: str,
        region: str,
        indicator: str,
        name: str,
        unit: str,
    ) -> Optional[dict]:
        """Fetch latest 2 observations for an ECB series key (flow/key format).

        Returns a normalized dict or None on any failure.
        """
        flow, key = series_key.split("/", 1)
        url = f"{_BASE_URL}/{flow}/{key}"
        try:
            resp = requests.get(
                url,
                params={"format": "jsondata", "lastNObservations": "2"},
                headers={"Accept": "application/json"},
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            return self._parse(resp.json(), series_key, region, indicator, name, unit)
        except Exception as exc:
            logger.warning("EcbProvider: failed for %s: %s", series_key, exc)
            return None

    def _parse(
        self,
        data: dict,
        series_key: str,
        region: str,
        indicator: str,
        name: str,
        unit: str,
    ) -> Optional[dict]:
        try:
            datasets = data.get("dataSets", [])
            if not datasets:
                return None
            series_map = datasets[0].get("series", {})
            if not series_map:
                return None
            # First series key
            series_data = next(iter(series_map.values()))
            obs = series_data.get("observations", {})
            if not obs:
                return None

            # Observation keys are "0", "1", ... sorted descending by lastNObservations
            obs_dims = (
                data.get("structure", {})
                    .get("dimensions", {})
                    .get("observation", [{}])[0]
                    .get("values", [])
            )

            sorted_keys = sorted(obs.keys(), key=int)
            latest_key = sorted_keys[-1]
            prev_key = sorted_keys[-2] if len(sorted_keys) >= 2 else None

            value = obs[latest_key][0]
            prev_value = obs[prev_key][0] if prev_key else None

            period_id = obs_dims[int(latest_key)]["id"] if int(latest_key) < len(obs_dims) else ""
            observation_date = period_id + "-01" if len(period_id) == 7 else period_id

            return {
                "series_id": series_key.replace("/", "_"),
                "region": region,
                "indicator": indicator,
                "name": name,
                "unit": unit,
                "source": "ECB",
                "value": float(value),
                "prev_value": float(prev_value) if prev_value is not None else None,
                "observation_date": observation_date,
                "period": _format_period(period_id),
            }
        except Exception as exc:
            logger.warning("EcbProvider: parse error for %s: %s", series_key, exc)
            return None

    def fetch_all(self) -> list[dict]:
        results = []
        for series_key, region, indicator, name, unit in ECB_SERIES:
            result = self.fetch_series(series_key, region, indicator, name, unit)
            if result:
                results.append(result)
        return results
```

- [ ] **Step 4: Verificar que los tests pasan**

```
cd backend
python -m pytest app/tests/test_ecb_provider.py -v
```

Esperado: 5 tests en verde.

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/economic_data/providers/ecb_provider.py \
        backend/app/tests/test_ecb_provider.py
git commit -m "feat(economy): add EcbProvider — HICP, Euríbor, BCE rate, current account"
```

---

### Task 2: `OecdProvider`

**Files:**
- Create: `backend/app/modules/economic_data/providers/oecd_provider.py`
- Create: `backend/app/tests/test_oecd_provider.py`

**Interfaces:**
- Produces: `OecdProvider.fetch_series(dataset, key, region, indicator, name, unit) -> Optional[dict]`
- Produces: `OecdProvider.fetch_all() -> list[dict]`
- Rol: siempre **validador** — nunca fuente primaria.

- [ ] **Step 1: Escribir los tests**

Crear `backend/app/tests/test_oecd_provider.py`:

```python
from unittest.mock import MagicMock, patch
import pytest


def _make_oecd_json(value: float, prev_value: float = 3.5) -> dict:
    return {
        "dataSets": [{
            "series": {
                "0:0:0:0:0": {
                    "observations": {
                        "0": [prev_value, 0],
                        "1": [value, 0],
                    }
                }
            }
        }],
        "structure": {
            "dimensions": {
                "observation": [{
                    "id": "TIME_PERIOD",
                    "values": [{"id": "2026-03"}, {"id": "2026-04"}],
                }]
            }
        }
    }


def test_fetch_series_parses_value():
    from app.modules.economic_data.providers.oecd_provider import OecdProvider
    provider = OecdProvider()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = _make_oecd_json(2.1, 2.3)

    with patch("app.modules.economic_data.providers.oecd_provider.requests.get", return_value=mock_resp):
        result = provider.fetch_series("PRICES_CPI", "ESP.CPI.IXOBSA._T.M", "ES", "inflation", "Inflación ES OCDE", "%")

    assert result is not None
    assert result["value"] == 2.1
    assert result["source"] == "OECD"


def test_fetch_series_returns_none_on_empty():
    from app.modules.economic_data.providers.oecd_provider import OecdProvider
    provider = OecdProvider()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"dataSets": [{"series": {}}], "structure": {"dimensions": {"observation": [{"id": "TIME_PERIOD", "values": []}]}}}

    with patch("app.modules.economic_data.providers.oecd_provider.requests.get", return_value=mock_resp):
        result = provider.fetch_series("PRICES_CPI", "ESP.CPI.IXOBSA._T.M", "ES", "inflation", "Test", "%")

    assert result is None


def test_fetch_series_returns_none_on_http_error():
    from app.modules.economic_data.providers.oecd_provider import OecdProvider
    provider = OecdProvider()

    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = Exception("503")

    with patch("app.modules.economic_data.providers.oecd_provider.requests.get", return_value=mock_resp):
        result = provider.fetch_series("BAD", "BAD", "ES", "inflation", "Test", "%")

    assert result is None


def test_fetch_series_returns_none_on_timeout():
    from app.modules.economic_data.providers.oecd_provider import OecdProvider
    import requests as req
    provider = OecdProvider()

    with patch("app.modules.economic_data.providers.oecd_provider.requests.get", side_effect=req.Timeout):
        result = provider.fetch_series("PRICES_CPI", "ESP.CPI.IXOBSA._T.M", "ES", "inflation", "Test", "%")

    assert result is None


def test_fetch_all_returns_list():
    from app.modules.economic_data.providers.oecd_provider import OecdProvider
    provider = OecdProvider()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = _make_oecd_json(2.1)

    with patch("app.modules.economic_data.providers.oecd_provider.requests.get", return_value=mock_resp):
        results = provider.fetch_all()

    assert isinstance(results, list)
```

- [ ] **Step 2: Verificar que fallan**

```
cd backend
python -m pytest app/tests/test_oecd_provider.py -v
```

Esperado: `ImportError`.

- [ ] **Step 3: Implementar `OecdProvider`**

Crear `backend/app/modules/economic_data/providers/oecd_provider.py`:

```python
"""OECD SDMX-JSON provider (no API key required). Used as validator only.

API base: https://sdmx.oecd.org/public/rest/data/{agency},{dataflow}/{key}
"""
from __future__ import annotations

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_BASE_URL = "https://sdmx.oecd.org/public/rest/data"
_AGENCY = "OECD"
_TIMEOUT = 15

_MONTHS_ES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
              "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# (dataset, key, region, indicator, name, unit)
OECD_SERIES: list[tuple[str, str, str, str, str, str]] = [
    ("DSD_PRICES@DF_PRICES_ALL", "ESP.CPI.IXOBSA._T.M", "ES", "inflation",    "Inflación España (OCDE)",    "%"),
    ("DSD_PRICES@DF_PRICES_ALL", "EA19.CPI.IXOBSA._T.M","EA", "inflation",    "Inflación Eurozona (OCDE)",  "%"),
    ("DSD_PRICES@DF_PRICES_ALL", "USA.CPI.IXOBSA._T.M", "US", "inflation",    "Inflación EEUU (OCDE)",      "%"),
    ("DSD_LFS@DF_LFS_INDIC",     "ESP.UNE_RATE.M",       "ES", "unemployment", "Paro España (OCDE)",         "%"),
    ("DSD_LFS@DF_LFS_INDIC",     "G-20.UNE_RATE.M",      "EA", "unemployment", "Paro Eurozona (OCDE)",       "%"),
    ("DSD_LFS@DF_LFS_INDIC",     "USA.UNE_RATE.M",       "US", "unemployment", "Paro EEUU (OCDE)",           "%"),
]


def _format_period(period_id: str) -> str:
    try:
        if len(period_id) == 7:
            year, month = int(period_id[:4]), int(period_id[5:7])
            return f"{_MONTHS_ES[month]} {year}"
    except (ValueError, IndexError):
        pass
    return period_id


class OecdProvider:
    def fetch_series(
        self,
        dataset: str,
        key: str,
        region: str,
        indicator: str,
        name: str,
        unit: str,
    ) -> Optional[dict]:
        url = f"{_BASE_URL}/{_AGENCY},{dataset}/{key}"
        try:
            resp = requests.get(
                url,
                params={"format": "jsondata", "lastNObservations": "2"},
                headers={"Accept": "application/json"},
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            return self._parse(resp.json(), dataset, key, region, indicator, name, unit)
        except Exception as exc:
            logger.warning("OecdProvider: failed for %s/%s: %s", dataset, key, exc)
            return None

    def _parse(
        self,
        data: dict,
        dataset: str,
        key: str,
        region: str,
        indicator: str,
        name: str,
        unit: str,
    ) -> Optional[dict]:
        try:
            datasets = data.get("dataSets", [])
            if not datasets:
                return None
            series_map = datasets[0].get("series", {})
            if not series_map:
                return None
            series_data = next(iter(series_map.values()))
            obs = series_data.get("observations", {})
            if not obs:
                return None

            obs_dims = (
                data.get("structure", {})
                    .get("dimensions", {})
                    .get("observation", [{}])[0]
                    .get("values", [])
            )

            sorted_keys = sorted(obs.keys(), key=int)
            latest_key = sorted_keys[-1]
            prev_key = sorted_keys[-2] if len(sorted_keys) >= 2 else None

            value = obs[latest_key][0]
            prev_value = obs[prev_key][0] if prev_key else None

            period_id = obs_dims[int(latest_key)]["id"] if int(latest_key) < len(obs_dims) else ""
            observation_date = period_id + "-01" if len(period_id) == 7 else period_id

            series_id = f"OECD_{dataset}_{key}".replace("@", "_").replace(".", "_")
            return {
                "series_id": series_id,
                "region": region,
                "indicator": indicator,
                "name": name,
                "unit": unit,
                "source": "OECD",
                "value": float(value),
                "prev_value": float(prev_value) if prev_value is not None else None,
                "observation_date": observation_date,
                "period": _format_period(period_id),
            }
        except Exception as exc:
            logger.warning("OecdProvider: parse error for %s: %s", key, exc)
            return None

    def fetch_all(self) -> list[dict]:
        results = []
        for dataset, key, region, indicator, name, unit in OECD_SERIES:
            result = self.fetch_series(dataset, key, region, indicator, name, unit)
            if result:
                results.append(result)
        return results
```

- [ ] **Step 4: Verificar que pasan**

```
cd backend
python -m pytest app/tests/test_oecd_provider.py -v
```

Esperado: 5 tests en verde.

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/economic_data/providers/oecd_provider.py \
        backend/app/tests/test_oecd_provider.py
git commit -m "feat(economy): add OecdProvider — inflation, unemployment (validator only)"
```

---

### Task 3: `WorldBankProvider`

**Files:**
- Create: `backend/app/modules/economic_data/providers/worldbank_provider.py`
- Create: `backend/app/tests/test_worldbank_provider.py`

**Interfaces:**
- Produces: `WorldBankProvider.fetch_indicator(iso3, wb_indicator, series_id, region, indicator, name, unit) -> Optional[dict]`
- Produces: `WorldBankProvider.fetch_all() -> list[dict]`
- Nota: datos anuales — el `observation_date` será el año más reciente disponible.

- [ ] **Step 1: Escribir los tests**

Crear `backend/app/tests/test_worldbank_provider.py`:

```python
from unittest.mock import MagicMock, patch
import pytest


def _make_wb_json(value: float, year: int = 2023) -> list:
    return [
        {"page": 1, "pages": 1, "per_page": 2, "total": 10},
        [
            {"date": str(year), "value": value, "country": {"id": "ESP", "value": "Spain"}},
            {"date": str(year - 1), "value": value - 2, "country": {"id": "ESP", "value": "Spain"}},
        ]
    ]


def test_fetch_indicator_parses_annual_value():
    from app.modules.economic_data.providers.worldbank_provider import WorldBankProvider
    provider = WorldBankProvider()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = _make_wb_json(113.5, 2023)

    with patch("app.modules.economic_data.providers.worldbank_provider.requests.get", return_value=mock_resp):
        result = provider.fetch_indicator("ESP", "GC.DOD.TOTL.GD.ZS", "WB_DEBT_ES", "ES", "debt_gdp", "Deuda/PIB España", "%")

    assert result is not None
    assert result["value"] == 113.5
    assert result["source"] == "WorldBank"
    assert result["region"] == "ES"


def test_fetch_indicator_returns_none_on_empty_data():
    from app.modules.economic_data.providers.worldbank_provider import WorldBankProvider
    provider = WorldBankProvider()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"page": 1}, []]

    with patch("app.modules.economic_data.providers.worldbank_provider.requests.get", return_value=mock_resp):
        result = provider.fetch_indicator("ESP", "GC.DOD.TOTL.GD.ZS", "WB_DEBT_ES", "ES", "debt_gdp", "Test", "%")

    assert result is None


def test_fetch_indicator_returns_none_on_timeout():
    from app.modules.economic_data.providers.worldbank_provider import WorldBankProvider
    import requests as req
    provider = WorldBankProvider()

    with patch("app.modules.economic_data.providers.worldbank_provider.requests.get", side_effect=req.Timeout):
        result = provider.fetch_indicator("ESP", "GC.DOD.TOTL.GD.ZS", "WB_DEBT_ES", "ES", "debt_gdp", "Test", "%")

    assert result is None


def test_fetch_all_returns_list():
    from app.modules.economic_data.providers.worldbank_provider import WorldBankProvider
    provider = WorldBankProvider()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = _make_wb_json(100.0)

    with patch("app.modules.economic_data.providers.worldbank_provider.requests.get", return_value=mock_resp):
        results = provider.fetch_all()

    assert isinstance(results, list)
```

- [ ] **Step 2: Verificar que fallan**

```
cd backend
python -m pytest app/tests/test_worldbank_provider.py -v
```

- [ ] **Step 3: Implementar `WorldBankProvider`**

Crear `backend/app/modules/economic_data/providers/worldbank_provider.py`:

```python
"""World Bank Open Data provider (no API key required). Annual data only.

API: https://api.worldbank.org/v2/country/{iso3}/indicator/{indicator}?format=json&mrv=2
"""
from __future__ import annotations

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.worldbank.org/v2/country"
_TIMEOUT = 15

# (iso3, wb_indicator, series_id, region, indicator, name, unit)
WB_SERIES: list[tuple[str, str, str, str, str, str, str]] = [
    # Deuda/PIB
    ("ESP", "GC.DOD.TOTL.GD.ZS", "WB_DEBT_ES", "ES", "debt_gdp", "Deuda/PIB España",    "%"),
    ("EMU", "GC.DOD.TOTL.GD.ZS", "WB_DEBT_EA", "EA", "debt_gdp", "Deuda/PIB Eurozona",  "%"),
    ("USA", "GC.DOD.TOTL.GD.ZS", "WB_DEBT_US", "US", "debt_gdp", "Deuda/PIB EEUU",      "%"),
    # PIB per cápita (USD corrientes)
    ("ESP", "NY.GDP.PCAP.CD", "WB_GDPPC_ES", "ES", "gdp_per_capita", "PIB per cápita España (USD)",    "USD"),
    ("EMU", "NY.GDP.PCAP.CD", "WB_GDPPC_EA", "EA", "gdp_per_capita", "PIB per cápita Eurozona (USD)",  "USD"),
    ("USA", "NY.GDP.PCAP.CD", "WB_GDPPC_US", "US", "gdp_per_capita", "PIB per cápita EEUU (USD)",      "USD"),
]


class WorldBankProvider:
    def fetch_indicator(
        self,
        iso3: str,
        wb_indicator: str,
        series_id: str,
        region: str,
        indicator: str,
        name: str,
        unit: str,
    ) -> Optional[dict]:
        url = f"{_BASE_URL}/{iso3}/indicator/{wb_indicator}"
        try:
            resp = requests.get(
                url,
                params={"format": "json", "mrv": "2", "per_page": "2"},
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            return self._parse(resp.json(), series_id, region, indicator, name, unit)
        except Exception as exc:
            logger.warning("WorldBankProvider: failed for %s/%s: %s", iso3, wb_indicator, exc)
            return None

    def _parse(
        self,
        data: list,
        series_id: str,
        region: str,
        indicator: str,
        name: str,
        unit: str,
    ) -> Optional[dict]:
        try:
            if len(data) < 2 or not data[1]:
                return None
            observations = [o for o in data[1] if o.get("value") is not None]
            if not observations:
                return None

            latest = observations[0]
            prev = observations[1] if len(observations) >= 2 else None

            year = latest["date"]
            return {
                "series_id": series_id,
                "region": region,
                "indicator": indicator,
                "name": name,
                "unit": unit,
                "source": "WorldBank",
                "value": float(latest["value"]),
                "prev_value": float(prev["value"]) if prev else None,
                "observation_date": f"{year}-01-01",
                "period": year,
            }
        except Exception as exc:
            logger.warning("WorldBankProvider: parse error: %s", exc)
            return None

    def fetch_all(self) -> list[dict]:
        results = []
        for iso3, wb_indicator, series_id, region, indicator, name, unit in WB_SERIES:
            result = self.fetch_indicator(iso3, wb_indicator, series_id, region, indicator, name, unit)
            if result:
                results.append(result)
        return results
```

- [ ] **Step 4: Verificar que pasan**

```
cd backend
python -m pytest app/tests/test_worldbank_provider.py -v
```

Esperado: 4 tests en verde.

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/economic_data/providers/worldbank_provider.py \
        backend/app/tests/test_worldbank_provider.py
git commit -m "feat(economy): add WorldBankProvider — debt/GDP, GDP per capita"
```

---

### Task 4: `EconomicProviderRouter` + config YAML

**Files:**
- Create: `backend/app/modules/economic_data/economic_data_config.yaml`
- Create: `backend/app/modules/economic_data/provider_router.py`
- Create: `backend/app/tests/test_economic_router.py`

**Interfaces:**
- Produces: `EconomicProviderRouter.fetch_all() -> list[dict]`
- Cada dict tiene los campos de un indicator + `confidence_score: float`, `source_count: int`, `source_fallback: bool`.

- [ ] **Step 1: Crear el config YAML**

Crear `backend/app/modules/economic_data/economic_data_config.yaml`:

```yaml
# Authority mapping: qué provider es primario y cuáles son validadores por (region, indicator).
# Si el primario falla, el primer validador disponible asciende.
authority:
  ES:
    inflation:
      primary: ecb
      validators: [oecd, fred]
    core_inflation:
      primary: fred
      validators: [oecd]
    unemployment:
      primary: fred
      validators: [oecd]
    gdp:
      primary: fred
      validators: [oecd]
    bond_10y:
      primary: stooq
      validators: []
    euribor:
      primary: ecb
      validators: [stooq]
    debt_gdp:
      primary: worldbank
      validators: []
    gdp_per_capita:
      primary: worldbank
      validators: []

  EA:
    inflation:
      primary: ecb
      validators: [oecd, fred]
    core_inflation:
      primary: ecb
      validators: [fred]
    unemployment:
      primary: fred
      validators: [oecd]
    gdp:
      primary: fred
      validators: [oecd]
    policy_rate:
      primary: ecb
      validators: []
    bond_10y:
      primary: stooq
      validators: []
    euribor:
      primary: ecb
      validators: [stooq]
    current_account:
      primary: ecb
      validators: []
    debt_gdp:
      primary: worldbank
      validators: []
    gdp_per_capita:
      primary: worldbank
      validators: []

  US:
    inflation:
      primary: fred
      validators: [oecd]
    core_inflation:
      primary: fred
      validators: [oecd]
    unemployment:
      primary: fred
      validators: [oecd]
    gdp:
      primary: fred
      validators: [oecd]
    policy_rate:
      primary: fred
      validators: []
    bond_10y:
      primary: stooq
      validators: []
    debt_gdp:
      primary: worldbank
      validators: []
    gdp_per_capita:
      primary: worldbank
      validators: []

# Umbral de divergencia aceptable entre providers (en unidades del indicador)
divergence_threshold: 0.5
```

- [ ] **Step 2: Escribir los tests del router**

Crear `backend/app/tests/test_economic_router.py`:

```python
from unittest.mock import MagicMock, patch
import pytest


def _indicator(value: float, source: str = "FRED") -> dict:
    return {
        "series_id": "TEST_SERIES",
        "region": "ES",
        "indicator": "inflation",
        "name": "Test",
        "unit": "%",
        "source": source,
        "value": value,
        "prev_value": value - 0.1,
        "observation_date": "2026-05-01",
        "period": "mayo 2026",
    }


def test_primary_succeeds_no_validators_confidence_07():
    from app.modules.economic_data.provider_router import EconomicProviderRouter
    router = EconomicProviderRouter()

    with patch.object(router._ecb, "fetch_series", return_value=_indicator(2.4, "ECB")):
        with patch.object(router._oecd, "fetch_series", return_value=None):
            with patch.object(router._fred, "fetch_series", return_value=None):
                result = router._resolve_indicator(
                    primary="ecb", validators=[], series_id="TEST",
                    region="ES", indicator="inflation", name="Test", unit="%"
                )

    assert result is not None
    assert result["value"] == 2.4
    assert result["confidence_score"] == 0.7
    assert result["source_fallback"] is False
    assert result["source_count"] == 1


def test_primary_plus_one_validator_agree_confidence_09():
    from app.modules.economic_data.provider_router import EconomicProviderRouter
    router = EconomicProviderRouter()

    with patch.object(router._ecb, "fetch_series", return_value=_indicator(2.4, "ECB")):
        with patch.object(router._oecd, "fetch_series", return_value=_indicator(2.45, "OECD")):
            result = router._resolve_indicator(
                primary="ecb", validators=["oecd"], series_id="TEST",
                region="ES", indicator="inflation", name="Test", unit="%"
            )

    assert result["confidence_score"] >= 0.9
    assert result["source_count"] == 2


def test_validators_diverge_reduces_confidence():
    from app.modules.economic_data.provider_router import EconomicProviderRouter
    router = EconomicProviderRouter()

    with patch.object(router._ecb, "fetch_series", return_value=_indicator(2.4, "ECB")):
        with patch.object(router._oecd, "fetch_series", return_value=_indicator(3.5, "OECD")):
            result = router._resolve_indicator(
                primary="ecb", validators=["oecd"], series_id="TEST",
                region="ES", indicator="inflation", name="Test", unit="%"
            )

    assert result["confidence_score"] < 0.9


def test_primary_fails_fallback_to_validator():
    from app.modules.economic_data.provider_router import EconomicProviderRouter
    router = EconomicProviderRouter()

    with patch.object(router._ecb, "fetch_series", return_value=None):
        with patch.object(router._oecd, "fetch_series", return_value=_indicator(2.1, "OECD")):
            result = router._resolve_indicator(
                primary="ecb", validators=["oecd"], series_id="TEST",
                region="ES", indicator="inflation", name="Test", unit="%"
            )

    assert result is not None
    assert result["source_fallback"] is True
    assert result["value"] == 2.1


def test_all_fail_returns_none():
    from app.modules.economic_data.provider_router import EconomicProviderRouter
    router = EconomicProviderRouter()

    with patch.object(router._ecb, "fetch_series", return_value=None):
        with patch.object(router._oecd, "fetch_series", return_value=None):
            with patch.object(router._fred, "fetch_series", return_value=None):
                result = router._resolve_indicator(
                    primary="ecb", validators=["oecd", "fred"], series_id="TEST",
                    region="EA", indicator="inflation", name="Test", unit="%"
                )

    assert result is None


def test_fetch_all_returns_list_of_dicts():
    from app.modules.economic_data.provider_router import EconomicProviderRouter
    router = EconomicProviderRouter()

    with patch.object(router, "_resolve_indicator", return_value=_indicator(2.0) | {"confidence_score": 0.9, "source_count": 2, "source_fallback": False}):
        results = router.fetch_all()

    assert isinstance(results, list)
```

- [ ] **Step 3: Verificar que los tests fallan**

```
cd backend
python -m pytest app/tests/test_economic_router.py -v
```

Esperado: `ImportError`.

- [ ] **Step 4: Implementar `EconomicProviderRouter`**

Crear `backend/app/modules/economic_data/provider_router.py`:

```python
"""EconomicProviderRouter — authority-based cross-validation for macro indicators."""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import yaml

from app.modules.economic_data.providers.ecb_provider import EcbProvider, ECB_SERIES
from app.modules.economic_data.providers.fred_provider import FredProvider, SERIES_CATALOGUE
from app.modules.economic_data.providers.oecd_provider import OecdProvider, OECD_SERIES
from app.modules.economic_data.providers.stooq_macro_provider import StooqMacroProvider
from app.modules.economic_data.providers.worldbank_provider import WorldBankProvider, WB_SERIES

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent / "economic_data_config.yaml"
_VALIDATOR_TIMEOUT = 8.0


def _load_config() -> dict:
    with open(_CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


class EconomicProviderRouter:
    def __init__(self) -> None:
        self._config = _load_config()
        self._divergence_threshold: float = self._config.get("divergence_threshold", 0.5)
        self._ecb = EcbProvider()
        self._oecd = OecdProvider()
        self._worldbank = WorldBankProvider()
        self._fred = FredProvider()
        self._stooq = StooqMacroProvider()

    def _get_provider(self, name: str):
        return {
            "ecb": self._ecb,
            "oecd": self._oecd,
            "worldbank": self._worldbank,
            "fred": self._fred,
            "stooq": self._stooq,
        }.get(name)

    def _call_provider(self, provider_name: str, series_id: str, region: str, indicator: str, name: str, unit: str) -> Optional[dict]:
        """Call the right method on each provider."""
        provider = self._get_provider(provider_name)
        if provider is None:
            return None

        if provider_name == "ecb":
            # Look up the ECB series key for this series_id
            for skey, r, ind, n, u in ECB_SERIES:
                sid = skey.replace("/", "_")
                if sid == series_id and r == region and ind == indicator:
                    return self._ecb.fetch_series(skey, region, indicator, name, unit)
            return None

        if provider_name == "oecd":
            for dataset, key, r, ind, n, u in OECD_SERIES:
                if r == region and ind == indicator:
                    return self._oecd.fetch_series(dataset, key, region, indicator, name, unit)
            return None

        if provider_name == "worldbank":
            for iso3, wb_indicator, sid, r, ind, n, u in WB_SERIES:
                if sid == series_id and r == region and ind == indicator:
                    return self._worldbank.fetch_indicator(iso3, wb_indicator, series_id, region, indicator, name, unit)
            return None

        if provider_name == "fred":
            for sid, r, ind, n, u in SERIES_CATALOGUE:
                if r == region and ind == indicator:
                    obs = self._fred.fetch_series(sid)
                    if obs:
                        return {
                            "series_id": sid, "region": r, "indicator": ind,
                            "name": n, "unit": u, "source": "FRED", **obs,
                        }
            return None

        if provider_name == "stooq":
            results = self._stooq.fetch_all()
            for r in results:
                if r.get("region") == region and r.get("indicator") == indicator:
                    return r
            return None

        return None

    def _calc_confidence(self, primary_value: float, validator_results: list[dict]) -> tuple[float, int]:
        if not validator_results:
            return 0.7, 1
        valid = [v for v in validator_results if v.get("value") is not None]
        agreeing = sum(1 for v in valid if abs(v["value"] - primary_value) <= self._divergence_threshold)
        diverging = len(valid) - agreeing
        base = 0.7 + 0.2 * (agreeing / max(len(valid), 1))
        penalty = 0.2 * diverging
        return round(max(0.0, min(1.0, base - penalty)), 2), 1 + len(valid)

    def _resolve_indicator(
        self,
        primary: str,
        validators: list[str],
        series_id: str,
        region: str,
        indicator: str,
        name: str,
        unit: str,
    ) -> Optional[dict]:
        primary_result = self._call_provider(primary, series_id, region, indicator, name, unit)

        if primary_result is None:
            for vname in validators:
                result = self._call_provider(vname, series_id, region, indicator, name, unit)
                if result is not None:
                    result["confidence_score"] = 0.7
                    result["source_count"] = 1
                    result["source_fallback"] = True
                    return result
            return None

        # Run validators in parallel
        validator_results: list[dict] = []
        if validators:
            with ThreadPoolExecutor(max_workers=len(validators)) as ex:
                futures = {
                    ex.submit(self._call_provider, vname, series_id, region, indicator, name, unit): vname
                    for vname in validators
                }
                for future in as_completed(futures, timeout=_VALIDATOR_TIMEOUT):
                    try:
                        r = future.result(timeout=_VALIDATOR_TIMEOUT)
                        if r is not None:
                            validator_results.append(r)
                    except Exception:
                        pass

        confidence, source_count = self._calc_confidence(primary_result["value"], validator_results)
        primary_result["confidence_score"] = confidence
        primary_result["source_count"] = source_count
        primary_result["source_fallback"] = False
        return primary_result

    def fetch_all(self) -> list[dict]:
        """Fetch all configured indicators using authority routing."""
        authority_cfg: dict = self._config.get("authority", {})
        results: list[dict] = []

        for region, indicators in authority_cfg.items():
            for indicator, routing in indicators.items():
                primary = routing.get("primary", "fred")
                validators = routing.get("validators", [])

                # Determine series_id, name, unit from the primary provider catalogue
                series_id, name, unit = self._lookup_series_meta(region, indicator, primary)
                if series_id is None:
                    continue

                result = self._resolve_indicator(primary, validators, series_id, region, indicator, name, unit)
                if result:
                    results.append(result)

        return results

    def _lookup_series_meta(self, region: str, indicator: str, primary: str) -> tuple[Optional[str], str, str]:
        """Find series_id, name, unit for a (region, indicator) in the primary provider."""
        if primary == "ecb":
            for skey, r, ind, name, unit in ECB_SERIES:
                if r == region and ind == indicator:
                    return skey.replace("/", "_"), name, unit
        if primary == "fred":
            for sid, r, ind, name, unit in SERIES_CATALOGUE:
                if r == region and ind == indicator:
                    return sid, name, unit
        if primary == "worldbank":
            for _, _, sid, r, ind, name, unit in WB_SERIES:
                if r == region and ind == indicator:
                    return sid, name, unit
        if primary == "stooq":
            from app.modules.economic_data.providers.stooq_macro_provider import MACRO_MARKET_SYMBOLS
            for sym, r, ind, name, unit in MACRO_MARKET_SYMBOLS:
                if r == region and ind == indicator:
                    return sym, name, unit
        if primary == "oecd":
            for _, _, r, ind, name, unit in OECD_SERIES:
                if r == region and ind == indicator:
                    return f"OECD_{region}_{indicator}", name, unit
        return None, indicator, "%"
```

- [ ] **Step 5: Verificar que los tests pasan**

```
cd backend
python -m pytest app/tests/test_economic_router.py -v
```

Esperado: 6 tests en verde.

- [ ] **Step 6: Commit**

```bash
git add backend/app/modules/economic_data/economic_data_config.yaml \
        backend/app/modules/economic_data/provider_router.py \
        backend/app/tests/test_economic_router.py
git commit -m "feat(economy): add EconomicProviderRouter with authority-based cross-validation"
```

---

### Task 5: Actualizar schemas, repository y service

**Files:**
- Modify: `backend/app/modules/economic_data/schemas.py`
- Modify: `backend/app/modules/economic_data/repository.py`
- Modify: `backend/app/modules/economic_data/service.py`

**Interfaces:**
- `IndicatorOut` añade: `confidence_score: float = 0.7`, `source_count: int = 1`, `source_fallback: bool = False`.
- `IndicatorTypeT` añade los nuevos tipos: `"debt_gdp"`, `"gdp_per_capita"`, `"current_account"`.
- `service._do_refresh()` delega en `EconomicProviderRouter` en lugar de llamar a FRED/Stooq directamente.
- `repository.upsert_indicator` acepta `confidence_score`, `source_count`, `source_fallback`.

- [ ] **Step 1: Actualizar `schemas.py`**

Reemplazar el contenido de `backend/app/modules/economic_data/schemas.py`:

```python
from typing import Literal, Optional

from pydantic import BaseModel

RegionT = Literal["ES", "EA", "US", "GLOBAL"]
IndicatorTypeT = Literal[
    "inflation",
    "core_inflation",
    "unemployment",
    "gdp",
    "gdp_per_capita",
    "policy_rate",
    "bond_10y",
    "euribor",
    "index",
    "forex",
    "debt_gdp",
    "current_account",
]
InterpretationT = Literal["favorable", "neutral", "adverse", "no_data"]


class IndicatorOut(BaseModel):
    series_id: str
    region: RegionT
    indicator: IndicatorTypeT
    name: str
    value: Optional[float]
    prev_value: Optional[float]
    change: Optional[float]
    period: str
    unit: str
    source: str
    observation_date: str
    is_stale: bool = False
    confidence_score: float = 0.7
    source_count: int = 1
    source_fallback: bool = False


class RegionSnapshotOut(BaseModel):
    region: RegionT
    indicators: list[IndicatorOut]


class MacroSnapshotOut(BaseModel):
    spain: RegionSnapshotOut
    eurozone: RegionSnapshotOut
    us: RegionSnapshotOut
    last_refreshed: str


class ImpactItem(BaseModel):
    title: str
    macro_value: Optional[float]
    personal_value: Optional[float]
    delta: Optional[float]
    interpretation: InterpretationT
    description: str


class PersonalImpactOut(BaseModel):
    inflation_vs_savings: ImpactItem
    rates_vs_liquidity: ImpactItem
    market_vs_portfolio: ImpactItem
    purchasing_power: ImpactItem
```

- [ ] **Step 2: Actualizar `repository.py`**

Añadir las columnas nuevas a la DDL y a `upsert_indicator`. Reemplazar el contenido completo:

```python
"""DuckDB-backed cache for economic indicator data."""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Optional

import duckdb

from app.core.duckdb import get_duckdb

logger = logging.getLogger(__name__)

_conn: Optional[duckdb.DuckDBPyConnection] = None
_conn_lock = threading.Lock()
_ddl_initialized = False

_DDL = """
CREATE TABLE IF NOT EXISTS economic_indicators_cache (
    series_id        VARCHAR NOT NULL,
    region           VARCHAR NOT NULL,
    indicator        VARCHAR NOT NULL,
    name             VARCHAR NOT NULL,
    value            DOUBLE,
    prev_value       DOUBLE,
    period           VARCHAR,
    unit             VARCHAR NOT NULL DEFAULT '%',
    source           VARCHAR NOT NULL,
    observation_date DATE NOT NULL,
    downloaded_at    TIMESTAMP NOT NULL,
    confidence_score DOUBLE NOT NULL DEFAULT 0.7,
    source_count     INTEGER NOT NULL DEFAULT 1,
    source_fallback  BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (series_id, observation_date)
);
"""

_TTL_HOURS: dict[str, int] = {
    "inflation": 24,
    "core_inflation": 24,
    "unemployment": 24,
    "gdp": 48,
    "gdp_per_capita": 48,
    "policy_rate": 4,
    "bond_10y": 4,
    "euribor": 4,
    "index": 4,
    "forex": 4,
    "debt_gdp": 48,
    "current_account": 24,
}


def _get_conn() -> duckdb.DuckDBPyConnection:
    global _conn, _ddl_initialized
    if not _ddl_initialized:
        with _conn_lock:
            if not _ddl_initialized:
                conn = get_duckdb()
                conn.execute(_DDL)
                # Add columns to existing tables (idempotent migration)
                for col, definition in [
                    ("confidence_score", "DOUBLE NOT NULL DEFAULT 0.7"),
                    ("source_count", "INTEGER NOT NULL DEFAULT 1"),
                    ("source_fallback", "BOOLEAN NOT NULL DEFAULT FALSE"),
                ]:
                    try:
                        conn.execute(f"ALTER TABLE economic_indicators_cache ADD COLUMN {col} {definition}")
                    except Exception:
                        pass  # Column already exists
                _conn = conn
                _ddl_initialized = True
    return _conn  # type: ignore[return-value]


def upsert_indicator(
    series_id: str,
    region: str,
    indicator: str,
    name: str,
    value: Optional[float],
    prev_value: Optional[float],
    period: str,
    unit: str,
    source: str,
    observation_date: str,
    confidence_score: float = 0.7,
    source_count: int = 1,
    source_fallback: bool = False,
) -> None:
    conn = _get_conn()
    now = datetime.now(timezone.utc)
    conn.execute(
        """
        INSERT OR REPLACE INTO economic_indicators_cache
            (series_id, region, indicator, name, value, prev_value, period, unit,
             source, observation_date, downloaded_at,
             confidence_score, source_count, source_fallback)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [series_id, region, indicator, name, value, prev_value, period, unit,
         source, observation_date, now, confidence_score, source_count, source_fallback],
    )


def get_latest(series_id: str) -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute(
        """
        SELECT series_id, region, indicator, name, value, prev_value, period, unit,
               source, observation_date::VARCHAR, downloaded_at,
               confidence_score, source_count, source_fallback
        FROM economic_indicators_cache
        WHERE series_id = ?
        ORDER BY observation_date DESC
        LIMIT 1
        """,
        [series_id],
    ).fetchone()
    if row is None:
        return None
    cols = ["series_id", "region", "indicator", "name", "value", "prev_value",
            "period", "unit", "source", "observation_date", "downloaded_at",
            "confidence_score", "source_count", "source_fallback"]
    return dict(zip(cols, row))


def get_all_latest() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        """
        SELECT DISTINCT ON (series_id)
               series_id, region, indicator, name, value, prev_value, period, unit,
               source, observation_date::VARCHAR, downloaded_at,
               confidence_score, source_count, source_fallback
        FROM economic_indicators_cache
        ORDER BY series_id, observation_date DESC
        """
    ).fetchall()
    cols = ["series_id", "region", "indicator", "name", "value", "prev_value",
            "period", "unit", "source", "observation_date", "downloaded_at",
            "confidence_score", "source_count", "source_fallback"]
    return [dict(zip(cols, r)) for r in rows]


def is_stale(series_id: str, indicator: str) -> bool:
    cached = get_latest(series_id)
    if cached is None:
        return True
    ttl = _TTL_HOURS.get(indicator, 24)
    downloaded_at = cached["downloaded_at"]
    if isinstance(downloaded_at, str):
        downloaded_at = datetime.fromisoformat(downloaded_at)
    age_hours = (datetime.now(timezone.utc) - downloaded_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
    return age_hours > ttl
```

- [ ] **Step 3: Actualizar `service.py` — usar el router**

Localizar `_do_refresh()` en `backend/app/modules/economic_data/service.py` y reemplazar solo esa función:

```python
def _do_refresh() -> list[dict]:
    from app.modules.economic_data.provider_router import EconomicProviderRouter
    router = EconomicProviderRouter()
    fetched = router.fetch_all()

    for item in fetched:
        try:
            repo.upsert_indicator(
                series_id=item["series_id"],
                region=item["region"],
                indicator=item["indicator"],
                name=item["name"],
                value=item.get("value"),
                prev_value=item.get("prev_value"),
                period=item.get("period", ""),
                unit=item.get("unit", "%"),
                source=item["source"],
                observation_date=item["observation_date"],
                confidence_score=item.get("confidence_score", 0.7),
                source_count=item.get("source_count", 1),
                source_fallback=item.get("source_fallback", False),
            )
        except Exception as exc:
            logger.error("Failed to cache indicator %s: %s", item.get("series_id"), exc)

    return repo.get_all_latest()
```

También actualizar `_row_to_indicator` en `service.py` para incluir los campos nuevos:

```python
def _row_to_indicator(row: dict) -> IndicatorOut:
    value = row.get("value")
    prev_value = row.get("prev_value")
    change = round(value - prev_value, 4) if value is not None and prev_value is not None else None
    return IndicatorOut(
        series_id=row["series_id"],
        region=row["region"],
        indicator=row["indicator"],
        name=row["name"],
        value=value,
        prev_value=prev_value,
        change=change,
        period=row.get("period", ""),
        unit=row.get("unit", "%"),
        source=row.get("source", ""),
        observation_date=str(row.get("observation_date", "")),
        is_stale=repo.is_stale(row["series_id"], row["indicator"]),
        confidence_score=float(row.get("confidence_score", 0.7)),
        source_count=int(row.get("source_count", 1)),
        source_fallback=bool(row.get("source_fallback", False)),
    )
```

- [ ] **Step 4: Verificar tests de economic_data existentes**

```
cd backend
python -m pytest app/tests/test_economic_data.py -v
```

Esperado: verde (los tests existentes no deberían romperse).

- [ ] **Step 5: Verificar tests del router**

```
cd backend
python -m pytest app/tests/test_economic_router.py -v
```

Esperado: verde.

- [ ] **Step 6: Commit**

```bash
git add backend/app/modules/economic_data/schemas.py \
        backend/app/modules/economic_data/repository.py \
        backend/app/modules/economic_data/service.py
git commit -m "feat(economy): wire EconomicProviderRouter into service, add confidence fields"
```

---

### Task 6: Frontend — nuevos tipos y confidence badge en `IndicatorCard`

**Files:**
- Modify: `apps/desktop/src/lib/types/index.ts`
- Modify: `apps/desktop/src/features/economy/components/IndicatorCard.tsx`

**Interfaces:**
- `EconomicIndicator` añade `confidence_score`, `source_count`, `source_fallback`.
- `EconomicIndicatorType` añade `"debt_gdp"`, `"gdp_per_capita"`, `"current_account"`.
- `IndicatorCard` muestra badge de confianza: verde ≥0.9, amarillo ≥0.7, rojo <0.7.

- [ ] **Step 1: Actualizar `types/index.ts`**

Localizar el bloque `// ── Fase 5 — Economic Intelligence` y reemplazar `EconomicIndicatorType` y `EconomicIndicator`:

```ts
export type EconomicIndicatorType =
  | "inflation" | "core_inflation" | "unemployment" | "gdp"
  | "gdp_per_capita" | "policy_rate" | "bond_10y" | "euribor"
  | "index" | "forex" | "debt_gdp" | "current_account";

export interface EconomicIndicator {
  series_id: string;
  region: EconomicRegion;
  indicator: EconomicIndicatorType;
  name: string;
  value: number | null;
  prev_value: number | null;
  change: number | null;
  period: string;
  unit: string;
  source: string;
  observation_date: string;
  is_stale: boolean;
  confidence_score: number;
  source_count: number;
  source_fallback: boolean;
}
```

- [ ] **Step 2: Actualizar `IndicatorCard.tsx`**

Reemplazar el contenido completo de `apps/desktop/src/features/economy/components/IndicatorCard.tsx`:

```tsx
import type { EconomicIndicator } from "@/lib/types";

interface Props {
  indicator: EconomicIndicator;
  size?: "default" | "large";
}

function formatValue(value: number | null, unit: string): string {
  if (value === null) return "—";
  const decimals = unit === "pts" || unit === "BUSD" || unit === "M€" || unit === "USD" ? 0 : 2;
  return value.toLocaleString("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function formatChange(change: number | null, unit: string): string {
  if (change === null) return "";
  const prefix = change > 0 ? "▲ +" : change < 0 ? "▼ " : "";
  const decimals = unit === "pts" ? 0 : 2;
  return `${prefix}${change.toLocaleString("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })} ${unit === "pts" ? "pts" : unit === "USD" ? "" : "pp"}`;
}

const INDICATOR_UNIT_SUFFIX: Record<string, string> = {
  "%": "%",
  "pts": " pts",
  "USD": "",
  "BUSD": " B$",
  "M€": " M€",
};

function ConfidenceBadge({ score, fallback }: { score: number; fallback: boolean }) {
  const color =
    score >= 0.9 ? "text-accent-teal bg-accent-teal/10"
    : score >= 0.7 ? "text-accent-warning bg-accent-warning/10"
    : "text-accent-danger bg-accent-danger/10";

  const label = fallback ? "fallback" : `${Math.round(score * 100)}%`;

  return (
    <span className={`text-[9px] font-medium rounded px-1 py-0.5 flex-shrink-0 ${color}`}>
      {label}
    </span>
  );
}

export default function IndicatorCard({ indicator, size = "default" }: Props) {
  const positive = (indicator.change ?? 0) >= 0;
  const hasChange = indicator.change !== null;
  const isUnavailable = indicator.value === null;

  const unitSuffix = INDICATOR_UNIT_SUFFIX[indicator.unit] ?? indicator.unit;
  const valueStr = isUnavailable
    ? "—"
    : `${formatValue(indicator.value, indicator.unit)}${unitSuffix}`;

  return (
    <div
      className={[
        "rounded-xl border border-hairline-dark bg-surface-elevated p-4 flex flex-col gap-2",
        size === "large" ? "p-5" : "",
      ].join(" ")}
    >
      <div className="flex items-center justify-between gap-2">
        <span className={`text-stone truncate ${size === "large" ? "text-body-sm" : "text-caption"}`}>
          {indicator.name}
        </span>
        <div className="flex items-center gap-1 flex-shrink-0">
          {!isUnavailable && (
            <ConfidenceBadge score={indicator.confidence_score} fallback={indicator.source_fallback} />
          )}
          {indicator.is_stale && (
            <span className="text-[10px] text-amber-400 bg-amber-400/10 rounded px-1.5 py-0.5 flex-shrink-0">
              DESACT.
            </span>
          )}
        </div>
      </div>

      <div className={`font-semibold tabular-nums ${size === "large" ? "text-2xl" : "text-xl"} ${isUnavailable ? "text-stone" : "text-on-dark"}`}>
        {valueStr}
      </div>

      {hasChange && (
        <div className={`text-caption tabular-nums ${positive ? "text-accent-success" : "text-accent-danger"}`}>
          {formatChange(indicator.change, indicator.unit)}
          {indicator.period && (
            <span className="text-mute ml-1">vs {indicator.period}</span>
          )}
        </div>
      )}

      {isUnavailable && (
        <p className="text-[10px] text-stone leading-tight">
          Dato no disponible en este momento
        </p>
      )}

      <div className="text-[10px] text-mute mt-auto pt-1 border-t border-hairline-dark">
        {indicator.source} · {indicator.period}
        {indicator.source_count > 1 && (
          <span className="ml-1 text-mute">({indicator.source_count} fuentes)</span>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verificar que TypeScript compila**

```
cd apps/desktop
npx tsc --noEmit
```

Esperado: sin errores nuevos.

- [ ] **Step 4: Commit**

```bash
git add apps/desktop/src/lib/types/index.ts \
        apps/desktop/src/features/economy/components/IndicatorCard.tsx
git commit -m "feat(economy-ui): add confidence badge to IndicatorCard, expand indicator types"
```

---

### Task 7: Actualizar el roadmap

**Files:**
- Modify: `docs/02_ROADMAP.md`

- [ ] **Step 1: Añadir Fase 5.1 al roadmap**

En la tabla de estado de `docs/02_ROADMAP.md`, añadir la fila:

```markdown
| 5.1 | Economic Intelligence Multi-Provider | ✅ Completa | rama actual |
```

Y añadir sección al final del bloque de Fase 5:

```markdown
## Fase 5.1 — Economic Intelligence Multi-Provider ✅

### Objetivo

Ampliar la inteligencia económica con tres nuevos providers gratuitos (ECB, OECD, World Bank)
y un router de autoridad que cross-valida indicadores entre fuentes.

### Incluye

- **EcbProvider** — HICP España/Eurozona, Euríbor 3M/12M, tipo BCE, balanza c/c.
- **OecdProvider** — inflación, paro (validador, 6 series).
- **WorldBankProvider** — deuda/PIB y PIB per cápita para ES/EA/US (datos anuales).
- **EconomicProviderRouter** — lógica de autoridad por (región, indicador), cross-validation paralela, `confidence_score` 0.7–1.0, fallback automático.
- **Schemas actualizados** — `IndicatorOut` con `confidence_score`, `source_count`, `source_fallback`.
- **Nuevos indicadores** — deuda/PIB, PIB per cápita, euríbor 12M, balanza c/c.
- **IndicatorCard** actualizado — badge de confianza (verde/amarillo/rojo).
- **20 tests** cubriendo los 4 providers y el router.
```

- [ ] **Step 2: Commit**

```bash
git add docs/02_ROADMAP.md
git commit -m "docs: add Fase 5.1 Economic Intelligence Multi-Provider to roadmap"
```
