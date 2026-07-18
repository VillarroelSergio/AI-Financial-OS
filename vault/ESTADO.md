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
- Corregidas dos alertas CodeQL de regex: el parseo de miles españoles ya no usa una expresión regular repetitiva y la importación de cartera rechaza textos de más de 100.000 caracteres; el sanitizador de IA elimina emojis sin usar un rango Unicode dentro de una expresión regular. Validación focalizada: 35 pruebas correctas y Ruff correcto. Evidencia en [[docs/testing/codeql_regex_guardrails.tdd]].
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
