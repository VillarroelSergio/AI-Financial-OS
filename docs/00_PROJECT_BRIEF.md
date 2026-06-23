# 00 — Project Brief

## Nombre del proyecto

AI Financial OS.

Nombre alternativo futuro posible: Finanze OS.

## Visión

AI Financial OS es una aplicación de escritorio moderna para Windows, local-first, diseñada para centralizar, visualizar y analizar las finanzas personales del usuario mediante datos importados manualmente e inteligencia artificial local.

No es una app de contabilidad tradicional, ni un chatbot financiero. Es un centro de control financiero personal que combina:

- Finanzas personales.
- Gastos e ingresos.
- Patrimonio.
- Inversiones.
- Objetivos.
- Datos macroeconómicos.
- Datos de mercado.
- IA local para análisis contextual.

## Objetivo del producto

Ayudar al usuario a entender su situación financiera, detectar patrones, comparar periodos, proyectar escenarios y recibir explicaciones útiles basadas en sus propios datos.

## Objetivo técnico

Construir una aplicación realista para aprender y practicar:

- Arquitectura desktop moderna.
- Tauri + React + TypeScript.
- Backend local con Python + FastAPI.
- Persistencia local con SQLite.
- Analítica con DuckDB.
- IA local con Ollama y LM Studio.
- RAG futuro con ChromaDB.
- Dashboards interactivos.
- Importación de CSV.
- Diseño UI/UX premium.
- Vibe coding asistido por Claude Code.

## Alcance inicial

El MVP debe centrarse en:

- Dashboard financiero.
- Cuentas manuales.
- Importación manual por CSV.
- Importador específico para Monefy.
- Movimientos.
- Categorías.
- Gastos e ingresos.
- Patrimonio.
- Inversiones básicas manuales.
- Datos macro y mercado básicos consultables online y cacheados localmente.

La IA no es obligatoria en el MVP inicial. La arquitectura debe quedar preparada para ella.

## Decisiones cerradas

- La carga de datos personales será manual por archivo.
- No habrá automatización bancaria.
- No habrá scraping de bancos o brokers.
- No habrá lectura automática de email.
- La app se ejecutará en el ordenador del usuario.
- Seguridad básica en V1, escalable a cifrado posterior.
- Idioma inicial: español.
- Estética: dark premium.

## Fuentes personales previstas

- Monefy.
- BBVA.
- Revolut.
- Trade Republic.
- Finizens.
- Cuentas remuneradas.

## Fuentes económicas previstas

- España.
- Eurozona.
- Estados Unidos.

## Fuentes de mercado previstas

- IBEX 35.
- Euro Stoxx 50.
- STOXX Europe 600.
- S&P 500.
- Nasdaq 100.
- Dow Jones.
- MSCI World.
- EUR/USD.
- Bonos a 10 años.

## Principio rector

La aplicación debe mostrar primero lo importante, permitir profundizar después y utilizar la IA como capa contextual, nunca como sustituto de los cálculos deterministas.
