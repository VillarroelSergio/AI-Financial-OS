---
name: Rentabilidad reportada de fondos
description: Los fondos manuales conservan por separado la ganancia simple y el porcentaje reportado por la plataforma
metadata:
  type: project
---

En fondos manuales, la rentabilidad porcentual mostrada por una plataforma como Finizens
puede ser una métrica TWR/MWR y no tiene por qué coincidir con
`ganancia / aportado`. Por eso cada `FundValuationSnapshot` puede guardar
`reported_return_pct` como dato independiente.

La ganancia en euros se usa para derivar el aportado (`valor actual - ganancia`) y calcular
el P&L simple. La tabla de posiciones muestra `reported_return_pct` cuando existe; si no,
mantiene el porcentaje simple derivado del coste.

La tarjeta agregada de Fondos usa `fund_reported_return_percent`, calculado como media
ponderada de los últimos porcentajes reportados por el capital aportado a cada fondo. Así
no presenta el P&L simple como si fuera la métrica TWR/MWR de Finizens. La etiqueta visible
indica `reportada` para distinguirla.

El editor genérico de una posición se muestra como modal fijo. Antes se insertaba al inicio
de la página y, al pulsar `Editar` desde una fila inferior, quedaba fuera del viewport y
parecía que la acción no funcionaba.

El alta debe hacer `flush` del primer snapshot antes de sincronizar el holding porque
`SessionLocal` usa `autoflush=False`. Sin ese paso, el fondo aparece sin valor hasta que el
usuario registra de nuevo la misma valoración.

Relacionadas: [[project_investments_module]] · [[04_DATA_MODEL]] · [[11_API_CONTRACT]]

Tags: #módulo #inversiones #fondos #decisión #bugfix
