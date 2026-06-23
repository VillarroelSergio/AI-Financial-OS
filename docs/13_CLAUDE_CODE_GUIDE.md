# 13 — Claude Code Guide

## Rol de Claude Code

Claude Code actuará como implementador técnico del proyecto en Visual Studio Code. Debe trabajar como un ingeniero de software senior, respetando la arquitectura, el roadmap, el diseño UX/UI y las restricciones de seguridad.

## Antes de implementar

Claude debe leer estos documentos:

1. `00_PROJECT_BRIEF.md`.
2. `02_ROADMAP.md`.
3. `03_ARCHITECTURE.md`.
4. `04_DATA_MODEL.md`.
5. `05_IMPORT_STRATEGY.md`.
6. `08_UX_UI_GUIDELINES.md`.
7. `09_DESIGN_SYSTEM.md`.
8. `10_SECURITY_MODEL.md`.
11. `11_API_CONTRACT.md`.

## Reglas obligatorias

### Producto

- La app debe ser simple, bonita y fácil de usar.
- No sobrecargar la interfaz.
- Priorizar dashboards claros.
- Mantener IA como capa contextual.

### Arquitectura

- Usar Tauri + React + TypeScript en frontend.
- Usar FastAPI + Python en backend.
- Usar SQLite como base principal.
- Integrar DuckDB para analítica.
- Preparar arquitectura para ChromaDB sin implementarlo en fases tempranas.

### Seguridad

- No automatizar bancos.
- No implementar scraping.
- No leer email.
- No guardar credenciales bancarias.
- No enviar datos personales a servicios cloud.

### IA

- Preparar Ollama y LM Studio.
- Modelo objetivo Qwen.
- No permitir SQL libre generado por LLM.
- Usar tool calling controlado.
- No introducir IA antes de la fase correspondiente.

### UX/UI

- Dark Premium.
- Pocas métricas por pantalla.
- Empty states cuidados.
- Importación guiada paso a paso.
- Gráficas simples.
- Panel lateral para IA.

## Modo de trabajo

Claude debe implementar en bloques pequeños.

Cada bloque debe incluir:

1. Resumen de cambios.
2. Archivos modificados.
3. Cómo probarlo.
4. Riesgos o pendientes.

## No hacer

- No crear una app de trading.
- No convertir Economy en un portal de noticias.
- No meter IA como pantalla principal del producto.
- No crear un chatbot antes del dashboard.
- No usar APIs de bancos.
- No añadir autenticación compleja en V1.
- No usar datos mock como si fueran reales.

## Prioridad de implementación

1. Foundation.
2. Layout + Design System.
3. Backend health + DB.
4. Accounts/Categories/Transactions.
5. Dashboard Overview.
6. Import Center.
7. Monefy CSV importer.
8. Spending dashboard.
9. Investments basic.
10. Economy/Market basic.
11. IA local.

## Criterio de calidad visual

La aplicación debe poder enseñarse como un producto real desde la Fase 1, aunque tenga pocas funcionalidades.

La interfaz debe transmitir:

- Control.
- Claridad.
- Confianza.
- Privacidad.
- Modernidad.
