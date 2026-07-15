# 🎉 AI Financial OS v1.0.0

**Tu centro de control financiero personal — local-first, privado y con IA local opcional.**

---

## 📋 Resumen

¡Bienvenido a v1.0 de **AI Financial OS**! Tras meses de desarrollo e iteración, llegamos a la versión estable inicial: una app de escritorio completa para Windows que centraliza tus finanzas personales sin nube, sin scraping bancario, sin ceder credenciales.

Esta es la versión de producto mínimo viable (MVP) que cubre los cinco pilares de la visión: **Resumen → Explicación → Detalle → Acción**, con todos los módulos operacionales y el stack completamente renovado.

---

## ✨ Lo Que Llega

### 🎛️ Módulos Operacionales

| Módulo | Descripción |
|--------|------------|
| **Dashboard** | Patrimonio neto, ahorro neto, ritmo de gasto, últimos movimientos, objetivos e insights de un vistazo. |
| **Movimientos y Cuentas** | Ledger financiero con búsqueda, filtros y nombres legibles (sin exponer IDs internos). |
| **Gastos** | Desglose mensual por categoría, tasa de ahorro, comparativa interperiódica y detección de categorías anómalas. |
| **Inversiones** | Posiciones, precios, rentabilidad, calidad y cobertura de cartera, riesgo de concentración y **conciliación**. |
| **Mercados** | Terminal compacto: índices, cripto, materias primas, divisas y bonos con _quality score_ y última actualización. |
| **Economía** | Indicadores macro (IPC, Euríbor, Tipo BCE) de España, Eurozona y EE.UU., con impacto en finanzas personales. |
| **Objetivos** | Metas financieras y simulaciones de escenarios. |
| **Insights** | Recomendaciones deterministas basadas en tus datos. |
| **Planificación** | Presupuestos, transacciones recurrentes, facturas del hogar y previsión de _cashflow_. |
| **Importación** | Centro inteligente con _preview_, validación y confirmación antes de persistir (CSV/Excel + Monefy). |
| **RAG** | Indexa y consulta documentación financiera local sin subirla a la nube. |
| **Asistente IA** | Copiloto contextual con IA 100% local (Ollama/LM Studio); nunca SQL libre, nunca inventa cifras. |
| **Seguridad y Backups** | Hardening, backups locales de SQLite y verificación de integridad. |

### 🔒 Principios de Diseño

- **Local-first absoluto** — todos tus datos viven en tu equipo (SQLite). Nada se sube a la nube.
- **Importación manual y consciente** — sin automatización bancaria ni scraping no autorizado.
- **Cálculo determinista primero** — el backend calcula; la IA solo explica. La IA nunca inventa cifras.
- **IA 100% local y opcional** — Ollama o LM Studio. La app funciona completamente sin IA.
- **Diseño dark premium** en español.

---

## 🚀 Cambios Técnicos v1.0

### Backend (Python 3.11+ · FastAPI)
- Versionado unificado a **1.0.0** en metadatos y `/health`.
- **Módulos de core financiero**: accounts, transactions, investments, market_intelligence, insights, goals, budgets, planning, rag, ai, security.
- **Almacenamiento dual**: SQLite para datos transaccionales + Market Intelligence en WAL; DuckDB para analítica.
- **Datasources de mercado**: Yahoo Finance, Stooq (base); Alpha Vantage, Finnhub, FMP, TwelveData (ampliación).
- **Indicadores macro**: FRED, Polygon, EIA, AEMET para España, Eurozona y EE.UU.
- **Auto-backfill en primer arranque**: históricos de 12 meses para índices y cripto.

### Desktop (Tauri 2 · React 18 · TypeScript · Tailwind)
- **Interfaz renovada** bajo la propuesta de diseño **C·Atelier** (light-first, dark-compatible).
- **Componentes reactivos**: gráficos con Recharts, animaciones con Framer Motion.
- **Arquitectura modular**: features por pantalla (dashboard, investments, markets, economy, etc.).
- **Estado gestionado** con React hooks y APIs REST tipadas.

### Seguridad
- **Token de API opcional** (`FINOS_API_TOKEN`) con comparación de tiempo constante (`hmac.compare_digest`).
- **CSP de producción** restringe conexiones del frontend a `localhost` (backend + IA local).
- **Secretos fuera de git** — `.env` nunca se commitea; modelo de seguridad detallado en [docs/10_SECURITY_MODEL.md](10_SECURITY_MODEL.md).

### DevOps
- **Empaquetado unificado**: Tauri (MSI/NSIS) + backend Python vía PyInstaller.
- **Setup automático**: `setup.ps1` crea `backend/.env`, instala dependencias, prepara `data/`.
- **Desarrollo ágil**: `npm run dev` arranca backend + app de escritorio con un comando.

---

## 🎯 Cómo Empezar

### Instalación (Desarrollo)

```powershell
# 1. Setup — crea data/, backend/.env desde .env.example e instala dependencias
.\scripts\setup.ps1

# 2. Arrancar backend + app de escritorio (un comando)
npm run dev
```

### Instalación (Release)

Descarga el instalador MSI desde la sección de [Releases](https://github.com/) y ejecuta. La app:
- Crea `backend/.env` automáticamente con valores por defecto.
- Guarda tus datos en `backend/data/` (SQLite + DuckDB).
- Funciona completamente sin conexión a internet (salvo para actualizar datos de mercado/macro).

### Requisitos Previos

- **Node.js 20+**
- **Rust stable** (requerido por Tauri)
- **Python 3.11+**
- **uv** — gestor de paquetes Python

---

## 📖 Documentación Completa

La carpeta [`docs/`](./) contiene:
- **[03_ARCHITECTURE.md](03_ARCHITECTURE.md)** — visión técnica y capas.
- **[11_API_CONTRACT.md](11_API_CONTRACT.md)** — contrato de endpoints.
- **[10_SECURITY_MODEL.md](10_SECURITY_MODEL.md)** — modelo de seguridad y privacidad.
- **[05_DATA_MODEL.md](05_DATA_MODEL.md)** — esquema de SQLite.
- **Roadmap y notas por módulo** — estado, decisiones, pendientes.

---

## 🔐 Privacidad y Seguridad

| Aspecto | Garantía |
|--------|----------|
| **Datos personales** | Viven únicamente en tu equipo. Cero telemetría, cero nube obligatoria. |
| **Datos de mercado/macro** | Se consultan online pero se cachean localmente; nunca contienen datos personales. |
| **Credenciales** | Importación manual (CSV/Excel); sin acceso automático a cuentas bancarias. |
| **IA** | 100% local (Ollama/LM Studio); nunca consulta SQL libre, nunca inventa cifras. |
| **CSP de producción** | Restringe conexiones del frontend a `localhost`. |

---

## 📦 Descargas

Disponibles en la página de [Releases](https://github.com/):
- **AI-Financial-OS-1.0.0.msi** — Instalador Windows (recomendado para usuarios).
- **AI-Financial-OS-1.0.0-nsis.exe** — Ejecutable NSIS (alternativa).
- **Código fuente** — `.zip` y `.tar.gz` de la rama `main`.

---

## 🙏 Créditos

**AI Financial OS** es un proyecto de **Sergio Villarroel Fernandez**, con inspiración en las mejores prácticas de:
- Fintech personal (YNAB, Ledger, Beancount).
- IA local y privacidad-first (Ollama, LM Studio).
- Diseño de datos y visualización (Apache Arrow, DuckDB, Recharts).

Licencia: **MIT** © 2026.

---

## 🐛 Reporta Bugs · Solicita Funciones

¿Encontraste un problema? ¿Una idea? Abre un [Issue](https://github.com/) o un [Discussion](https://github.com/).

---

## 🎮 Próximas Fases (Roadmap 2026+)

Tras v1.0, la visión incluye:
- **Sincronización multi-device** (sincronización local-first).
- **Widgets de escritorio** para resúmenes rápidos.
- **Exportación a TurboTax/Contaplus** para impuestos.
- **Alertas y notificaciones** en eventos de portfolio.
- **API pública** para integraciones de terceros.

---

## ¡Gracias por ser parte de la v1.0! 🚀

Esperamos que **AI Financial OS** te ayude a tomar el control de tus finanzas personales.

**Disfruta de la privacidad. Disfruta de la claridad.**
