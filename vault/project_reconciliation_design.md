---
name: project_reconciliation_design
description: Diseño acordado de conciliación Monify↔bancos - Monify manda en analítica personal
metadata: 
  node_type: memory
  type: project
  originSessionId: 3c51531b-0cda-4919-ad0a-03d77b14a020
---

**PIVOTE 2026-07-04 (mismo día, sesión posterior): modelo de CARGA ÚNICA.**
El cruce heurístico Monefy↔bancos no convenció al usuario ("el cruce es imposible"). Decisión final:

1. El usuario importa UN solo archivo (Monefy, Revolut, BBVA o genérico); ese archivo ES su registro personal. Todo movimiento importado entra con `analytics_scope='personal'`, salvo transferencias (`excluded`).
2. Si el archivo no trae categorías (bancos), se infieren por comercio con `backend/app/modules/imports/auto_categorizer.py` (keyword→categoría de sistema; palabra suelta = prefijo de token, multiword = subcadena; genéricos de restauración al final).
3. El motor de conciliación (`imports/reconciliation.py`, endpoints /reconcile, /reconciliation, ReconciliationPage.tsx) quedó DORMIDO: sin pestaña en UI y nada crea scope 'pending' (la migración lo reconvierte a 'personal'). No borrar sin preguntar; podría reactivarse.
4. Monify siempre EUR aunque el CSV diga USD (force_currency en el perfil Monefy).
5. La analítica del dashboard filtra `analytics_scope = 'personal'`; los transfers (Recargas, Savings Vault, Traspasos, Revolut**) se marcan por patrones de perfil al importar.

**Why:** El matching heurístico genera desconfianza; con una única fuente los datos cuadran por construcción.

**How to apply:** No reintroducir cruces automáticos entre fuentes ni el estado 'pending'. Ver [[project-constraints]].


---
**Relacionadas:** [[project_investments_module]] · [[project_constraints]]

Tags: #módulo #decisión
