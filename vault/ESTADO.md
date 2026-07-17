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
- Rama de trabajo actual: `feature/mejoras-balance-inversiones-accesibilidad`

## En curso
- Hotfix del módulo de inversiones: fondos, reasignación de carteras, valoración de cuentas y coherencia del Resumen.

## Hecho recientemente
- Corregido el fallo común de CI de las PR #39 y #40: Tauri requería el recurso `binaries/backend` en un checkout limpio, pero el directorio vacío no se versionaba. Añadido `.gitkeep` permitido por `.gitignore`; `cargo check --locked` pasa localmente. Evidencia en [[docs/testing/tauri_ci_resources.tdd]].
- Unificado el movimiento de entrada en toda la aplicación: rutas, tarjetas, KPI, diálogos, drawers, popovers, avisos y filas pasan de opacidad 0 a 1 con movimiento sutil. Corregidos los conflictos de renderizado: las barras conservan su porcentaje, las tablas no animan `transform` y el filtro de movimientos mantiene la capa correcta. `prefers-reduced-motion` conserva un fundido breve. Contrato fuente actualizado; validación pendiente de permiso. Ver [[project_accessibility_and_investment_price_ux]].
- Retirado el cierre mensual de la interfaz del Balance General; el panel conserva activos, pasivos, patrimonio y evolución. Mejorado el modal de precios manuales para explicar el NAV por participación de fondos y calcular el valor resultante. Añadido ajuste persistente de tamaño de texto (compacto, normal, grande, muy grande) y elevada la escala base. Corregido Ajustes: faltaba el `ToastProvider`, que dejaba la pantalla en negro. La escala ya cubre aliases y tamaños arbitrarios de toda la app. Las tarjetas de todos los módulos entran desde abajo con escalonado breve y mantienen hover/press; barras de progreso y asignación se revelan desde la izquierda, sin anular `prefers-reduced-motion`. Corregido el contador de patrimonio en React StrictMode. Eliminada en escritorio la barra superior redundante con el nombre de la sección y sus divisores; el copiloto queda como control flotante y las pestañas conservan solo el indicador activo. Validación: build y contratos UI pasan; capturas dirigidas de Finanzas, Inversiones y Mercados verificadas visualmente; E2E aislada 26 PASS, 7 BLOCKED conocidos, sin errores de consola ni HTTP 5xx. Ver [[project_accessibility_and_investment_price_ux]].
- Corregida la alerta CodeQL de exposición de excepciones en copias de seguridad: el 404 ya no revela detalles internos y registra la causa en servidor. Evidencia en [[docs/testing/codeql_backup_error_exposure.tdd]].
- Fijadas las cinco Actions de CI a SHA completos, con sus versiones anotadas para Dependabot. Pendiente llevar el workflow a `main` y activar la política remota que obliga a usar SHA completos.
- Añadida la configuración semanal de Dependabot para `uv`, npm (aplicación y herramientas E2E), Cargo y GitHub Actions. Agrupa actualizaciones menores/parche y deja las mayores en PRs separadas. Pendiente commit/push para que GitHub la active.
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
