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
- Ejecutada la validación local completa: contratos E2E (33 flujos), casos negativos (15) y aislamiento pasan; la suite de navegador deja 26 PASS y 7 BLOCKED por fixtures/providers aún no deterministas, sin errores de consola ni HTTP 5xx. Pytest queda en 442 PASS y 8 FAIL reproducibles, sin fallos de infraestructura. El runner E2E ya lee contratos desde `vault/docs/testing/` y permite aislar artefactos con `E2E_OUTPUT_DIR`.
- Corregida la primera CI de GitHub Actions del PR #36: caché de `uv`, lint Ruff y recurso requerido por Tauri en checkouts limpios. Ruff y `cargo check --locked` pasan localmente; Pytest no se ejecutó. Pendiente commit/push y nueva ejecución remota.
- Bóveda operativa: `Home` + 8 MOCs + 32 docs migrados a `vault/docs/` + notas de memoria. Todos los wikilinks resuelven.
- Plantillas y glosario añadidos ([[templates/_template_nota_memoria]], [[GLOSARIO]]).
- Las cuentas remuneradas usan su holding como saldo canónico y computan una sola vez en Resumen, Balance General e IA; ver [[project_investment_account_valuation]].
- Las cuentas remuneradas y el efectivo quedan fuera del P&L sobre aportado de Inversiones, aunque permanecen en valor total y patrimonio.
- Restaurada la animación obligatoria de inicio de 2,4 s, eliminada de nuevo la carga diferida de rutas y configurada la ventana Windows para abrir maximizada; validación pendiente de permiso.
- Eliminado el lienzo blanco previo al arranque: la ventana se revela cuando React ya ha montado la experiencia de inicio y las capas nativa/HTML comparten fondo grafito; validación pendiente de permiso.

## Siguiente / pendiente
- Revisar y corregir los 8 contratos Pytest fallidos: `price_source` en activos, agregación de inversiones en Resumen, versión de `/health`, NAV manual, reconciliación de ahorro, candidatos de SpaceX, reasignación de divisa y rangos históricos cortos.
- Rotar API keys (ver [[project_v1_release_prep]]).
- Modelar la rentabilidad reportada de Finizens en el nivel cartera (Global/USA), no como agregado de fondos subyacentes.

## Convenciones que nunca se saltan
Ver [[project_constraints]] · [[feedback_commits_and_graphify]] · [[feedback_language_spanish]].

---
**Relacionadas:** [[Home]] · [[MEMORY]] · [[project_v1_release_prep]]

Tags: #estado #project
