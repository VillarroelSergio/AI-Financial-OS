# 26 - UX Functional QA & Product Intelligence Repair

## Objetivo

Fase 10.5 estabiliza la aplicacion como producto financiero usable antes de Packaging & Release. La prioridad es que cada modulo muestre estados honestos, datos trazables y acciones claras, sin errores tecnicos crudos ni datos seed/demo presentados como reales.

## Alcance P0

### Mercados

- La UI no debe mostrar `Failed to fetch` como mensaje principal.
- La API expone estado de snapshot (`ok`, `partial`, `empty`) y calidad media.
- Cada dato mantiene proveedor, calidad y fecha cuando existe.
- Si la ingesta falla, el frontend comunica que muestra ultimos datos disponibles si existen.

### Economia

- Los indicadores se separan por Espana, Eurozona y EEUU.
- Cada indicador expone fuente, periodo, unidad, calidad y `data_status`.
- Si varios indicadores de una region comparten mismo valor y periodo, se marcan como `requires_review` y bajan su calidad para evitar fallback silencioso.
- Impacto personal solo debe mostrarse cuando los datos base sean validos.

### Reconciliacion de cartera

- La pantalla debe entenderse como revision/calidad de cartera.
- Debe responder que posiciones estan confirmadas, estimadas, manuales, sin precio, con FX pendiente o requieren revision.
- Las acciones de correccion deben apuntar a precios, FX, instrumento ambiguo o dato manual.

### Movimientos

- No se muestran UUID internos al usuario.
- La pantalla debe soportar busqueda por descripcion, filtros por fecha, cuenta, categoria, tipo e importe.
- Crear, editar y eliminar requieren estados claros y confirmacion en eliminacion.

### Importar cartera

- El objetivo de producto es soportar capturas reales procesadas localmente.
- Texto pegado y entrada manual se mantienen como fallback.
- Ningun holding se crea sin confirmacion explicita.
- Las capturas no se guardan de forma permanente salvo decision explicita del usuario.

## Alcance P1

- Copiloto IA contextual por modulo, con datos usados, limites e insuficiencias visibles.
- Planificacion con deteccion asistida de recurrentes y conversion solo tras confirmacion.
- Objetivos con mensajes textuales de plazo, aportacion necesaria, escenarios e inflacion.
- Gastos con ranking, agrupacion de categorias pequenas, comparativa y drilldown.

## Alcance P2

- Seguimiento de suministros y facturas del hogar.
- Ajustes como centro de control local: backend, IA, RAG, backups, integridad, ruta de datos y privacidad.

## Reglas de producto

- Local-first.
- Sin scraping bancario ni de brokers.
- Sin automatizacion bancaria.
- Sin envio de datos financieros personales a servicios cloud no definidos.
- Sin recomendaciones financieras vinculantes.
- La IA usa datos preparados por servicios deterministas y no accede libremente a SQL.

## Bateria UX obligatoria

La fase debe documentar ejecucion o bloqueo para:

- Resumen: datos reales, parciales, insights y acciones.
- Gastos: pocas/muchas categorias, drilldown, comparativa y categoria vacia.
- Movimientos: busqueda, filtros, crear, editar y eliminar con confirmacion.
- Cuentas: crear, editar, desactivar y ver impacto patrimonial.
- CSV: importacion valida, invalida, preview, confirmacion y rollback.
- Inversiones: precios, manuales, sin precio, calidad de cartera y concentracion.
- Importar cartera: captura, texto, manual, ambiguedades, confirmar, cancelar y duplicados.
- Economia: Espana, Eurozona, EEUU, datos disponibles, parciales, ausentes e impacto personal.
- Mercados: primer acceso, cache, actualizacion, proveedor fallando y datos stale.
- Objetivos: simulacion, inflacion, aportacion, alcanzable y no alcanzable.
- Planificacion: presupuesto, recurrentes candidatos, confirmar, ignorar, calendario y cashflow.
- Insights: resumen mensual, filtros, fuentes, descartar y datos incompletos.
- Asistente IA: general, contextual, sin provider, datos insuficientes y datos usados.
- RAG: subir, consultar, fuentes y sin resultados.
- Ajustes: idioma, moneda, IA, backups, integridad y ruta local.

## Criterio de salida

Fase 11 no debe empezar hasta que no queden errores crudos en pantallas principales, no haya UUID internos visibles, los datos macro/mercado sean honestos sobre fuente/calidad/fecha y la bateria UX tenga resultado documentado con snapshots actualizados.
