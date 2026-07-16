---
name: ESTADO
description: Estado vivo del proyecto — punto único para saber dónde estamos al arrancar sesión
metadata:
  type: project
---

# 📍 Estado actual

> Nota **viva**: actualízala al cerrar cualquier tarea. Es lo primero que lee un agente al arrancar.

**Última actualización:** 2026-07-16

## Versión y rama
- Versión de código: **1.1.5**
- Rama de trabajo actual: `chore/github-actions-ci`

## En curso
- Hotfix del módulo de inversiones: fondos, reasignación de carteras, valoración de cuentas y coherencia del Resumen.

## Hecho recientemente
- Corregidos los ocho contratos desalineados que hacían fallar `Backend · Ruff y Pytest` en el PR #36. Validación local: 450/450 pruebas correctas y Ruff correcto; solo queda la advertencia conocida de deprecación de `httpx`. Evidencia en [[docs/testing/github-actions-backend-ci.tdd]].
- Ejecutada la validación local completa: contratos E2E (33 flujos), casos negativos (15) y aislamiento pasan; la suite de navegador deja 26 PASS y 7 BLOCKED por fixtures/providers aún no deterministas, sin errores de consola ni HTTP 5xx. La primera ejecución de Pytest reprodujo los 8 contratos desalineados que después quedaron corregidos. El runner E2E ya lee contratos desde `vault/docs/testing/` y permite aislar artefactos con `E2E_OUTPUT_DIR`.
- Corregida la primera CI de GitHub Actions del PR #36: caché de `uv`, lint Ruff y recurso requerido por Tauri en checkouts limpios. Ruff, Pytest y `cargo check --locked` pasan localmente. Pendiente commit/push y nueva ejecución remota.
- Bóveda operativa: `Home` + 8 MOCs + 32 docs migrados a `vault/docs/` + notas de memoria. Todos los wikilinks resuelven.
- Plantillas y glosario añadidos ([[templates/_template_nota_memoria]], [[GLOSARIO]]).
- Las cuentas remuneradas usan su holding como saldo canónico y computan una sola vez en Resumen, Balance General e IA; ver [[project_investment_account_valuation]].
- Las cuentas remuneradas y el efectivo quedan fuera del P&L sobre aportado de Inversiones, aunque permanecen en valor total y patrimonio.
- Restaurada la animación obligatoria de inicio de 2,4 s, eliminada de nuevo la carga diferida de rutas y configurada la ventana Windows para abrir maximizada; validación pendiente de permiso.
- Eliminado el lienzo blanco previo al arranque: la ventana se revela cuando React ya ha montado la experiencia de inicio y las capas nativa/HTML comparten fondo grafito; validación pendiente de permiso.

## Siguiente / pendiente
- Rotar API keys (ver [[project_v1_release_prep]]).
- Modelar la rentabilidad reportada de Finizens en el nivel cartera (Global/USA), no como agregado de fondos subyacentes.

## Convenciones que nunca se saltan
Ver [[project_constraints]] · [[feedback_commits_and_graphify]] · [[feedback_language_spanish]].

---
**Relacionadas:** [[Home]] · [[MEMORY]] · [[project_v1_release_prep]]

Tags: #estado #project
