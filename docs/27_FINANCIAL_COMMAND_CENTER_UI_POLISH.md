# Financial Command Center UI Polish

## Objetivo

Fase 10.5.UI eleva AI Financial OS hacia un centro de mando financiero premium, claro y accionable, manteniendo el stack React/Tailwind existente y el principio local-first.

## Patrones aplicados

- Canvas near-black con superficies elevadas tipo Mercury.
- `PageHeader` como cabecera comun para modulo, estado y acciones.
- `premium-card`, `mercury-panel`, `mercury-button` y `mercury-button-primary` como primitivas visuales compartidas.
- Badges compactos para estados de datos y calidad.
- Tablas con busqueda, filtros y nombres legibles cuando hay volumen de filas.
- Errores controlados orientados a usuario, sin mensajes crudos como estado principal.
- Radios de 8px, bordes finos y acento violet-blue reservado para acciones principales.

## Modulos tocados

- Resumen: hero ejecutivo y jerarquia de patrimonio, liquidez y ahorro.
- Gastos: agrupacion de categorias pequenas en "Otros" y controles visuales mas legibles.
- Movimientos: ledger con busqueda, filtros por tipo/cuenta/categoria y sin UUID visibles.
- Cuentas: cabecera de modulo, cards coherentes y edicion menos invasiva.
- Importacion: flujo guiado, estados de validacion y mensajes de error comprensibles.
- Inversiones: cabecera de portfolio desk y acciones primarias/secundarias ordenadas.
- Economia: cabecera macro, estado cacheado/actualizado y error controlado.
- Mercados: terminal compacto con calidad visible y contenedores coherentes.
- Planificacion: cabecera comun y tabs Mercury.
- Asistente IA: panel integrado, sidebar propia y command bar sobria.
- Ajustes: centro de control local para preferencias, IA, privacidad e integridad.

## Criterios de uso

- Cada pantalla debe responder que se ve, que dato importa, que estado tiene, que accion procede y donde profundizar.
- Las acciones primarias usan `mercury-button-primary`; las secundarias usan `mercury-button`.
- Los formularios inline deben estar contenidos en una superficie elevada, no dominar la pantalla por defecto.
- Las tablas no deben mostrar identificadores internos al usuario final.

## Validacion

- Build frontend ejecutado con `npm run build`.
- Queda pendiente regenerar snapshots UX completos cuando el backend y los datos demo esten disponibles.
