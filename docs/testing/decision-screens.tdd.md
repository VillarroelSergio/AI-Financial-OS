# Pantallas de decisión — evidencia TDD

## RED

- Se añadió `tools/ux-snapshot/test-ui-quality-contracts.ts` con contratos para el centrado de Mercados, filtros progresivos, acciones explícitas, cuentas desactualizadas, comparativa de gasto, señales del resumen y concentración de cartera.
- La primera ejecución falló porque Mercados no usaba un contenedor centrado compartido.

## GREEN

- `npm run test:ui-quality` (en `tools/ux-snapshot`): correcto.
- `npm run build` (en `apps/desktop`): correcto.
- `npm run snapshots:mercados` (en `tools/ux-snapshot`): 2/2 capturas generadas.

## Revisión visual

- `ux-snapshots/latest/markets.png`: el contenido queda alineado con el ancho y margen de las demás pantallas.
- `ux-snapshots/latest/transactions.png`, `spending.png`, `overview.png` e `investments.png`: revisión visual realizada tras los cambios principales.

## Acceso a herramientas secundarias

### RED

- Se ampliÃ³ el contrato de interfaz para exigir un acceso visible a Objetivos e Insights fuera de los cinco mÃ³dulos principales.
- `npm run test:ui-quality` fallÃ³ inicialmente porque la navegaciÃ³n solo conservaba las rutas, sin un punto de entrada visible.

### GREEN

- La barra lateral y la navegaciÃ³n mÃ³vil incluyen ahora el desplegable **MÃ¡s herramientas**, con accesos a Objetivos e Insights.
- `npm run test:ui-quality` (en `tools/ux-snapshot`): correcto.
- `npm run build` (en `apps/desktop`): correcto.

## Apertura inmediata de Ajustes

### RED

- El contrato de interfaz exigía precargar los datos de Ajustes durante el arranque, reutilizar esa carga al entrar y no bloquear la página con `if (loading)`.
- `npm run test:ui-quality` falló inicialmente porque Ajustes iniciaba seis consultas al montarse y mostraba un spinner a pantalla completa.

### GREEN

- `main.tsx` inicia `preloadSettingsOverview()` antes del primer render de React.
- Ajustes reutiliza `loadSettingsOverview()` y muestra su estructura de inmediato mientras se completa la carga.
- `npm run test:ui-quality` (en `tools/ux-snapshot`): correcto.
- `npm run build` (en `apps/desktop`): correcto.

## Entrada de la aplicacion y coherencia del Resumen

### Recorridos cubiertos

- Como usuario, quiero percibir una bienvenida breve cada vez que arranco la aplicacion, sin que retrase el acceso a mis datos.
- Como usuario, quiero que las tres senales principales del Resumen tengan el mismo peso visual y lleven a una accion concreta.

### RED

- Se amplio `tools/ux-snapshot/test-ui-quality-contracts.ts` para exigir el componente de entrada, su retirada automatica, una alternativa para reducir movimiento, la ausencia de "Centro de control privado" y una superficie compartida para Patrimonio neto.
- `npm run test:ui-quality` fallo inicialmente porque no existia `StartupExperience.tsx`.

### GREEN

- `StartupExperience` se monta una vez en cada arranque y se retira al acabar su propia animacion; no espera datos ni intercepta interacciones.
- El Resumen usa ahora tarjetas homogeneas y enlaza Patrimonio, Ahorro y Ritmo de gasto con cuentas o gastos.
- `npm run test:ui-quality` (en `tools/ux-snapshot`): correcto.
- `npm run build` (en `apps/desktop`): correcto, con el aviso existente de tamano de bundle.
- `npm run snapshots` (en `tools/ux-snapshot`): 21/21 capturas generadas; se reviso `ux-snapshots/latest/overview.png`.

| # | Garantia | Prueba | Tipo | Resultado |
|---|---|---|---|---|
| 1 | La entrada existe en cada montaje de la aplicacion y se retira al finalizar | `test:ui-quality-contracts.ts` | Contrato estatico | PASS |
| 2 | La entrada respeta reducir movimiento | `test:ui-quality-contracts.ts` | Contrato estatico | PASS |
| 3 | El encabezado no repite "Centro de control privado" | `test:ui-quality-contracts.ts` | Contrato estatico | PASS |
| 4 | Patrimonio neto comparte superficie con las demas senales y ofrece una accion | `test:ui-quality-contracts.ts` | Contrato estatico + captura | PASS |

## Correccion de coherencia, accesos y movimiento de arranque

### RED

- Se actualizaron los contratos para prohibir Objetivos e Insights en la barra lateral, exigir ambos accesos en el Dashboard, restaurar los tokens verde y rojo acordados y reemplazar el splash por movimiento del propio espacio de trabajo.
- `npm run test:ui-quality` fallo inicialmente porque la barra lateral aun incluia “Mas herramientas”.

### GREEN

- La navegacion conserva solo Dashboard, Movimientos y cuentas, Inversiones, Economia y Mercado; Objetivos e Insights quedan visibles en la columna del Dashboard.
- Verde jade: `#2F8F6B`; rojo granate: `#C95B66`. Los graficos y minigraficos que tenian valores directos fueron alineados a los mismos valores.
- El arranque anima rail y espacio de trabajo, sin overlay ni logotipo intermedio; con reducir movimiento activo no se inicia la transicion.
- `npm run test:ui-quality` (en `tools/ux-snapshot`): correcto.
- `npm run build` (en `apps/desktop`): correcto, con el aviso existente de tamano de bundle.
- `npm run snapshots` (en `tools/ux-snapshot`): 21/21 capturas generadas; se reviso `ux-snapshots/latest/overview.png`.

## Paleta y bienvenida de arranque

### RED

- El contrato exigia una escena de entrada propia y fallo al detectar que `StartupExperience` no contenia una composicion visual.

### GREEN

- Azul pizarra: `#5B7EA3`; ambar arcilla: `#C28A4A`. Ambos sustituyen los azules y naranjas electricos en tokens, categorias, graficos de cartera y seleccion de Ajustes.
- La bienvenida monta una tarjeta de marca con tres barras financieras y una traza que se compone y se retira en 720 ms. No usa spinner ni espera datos.
- `npm run --prefix tools/ux-snapshot test:ui-quality`: correcto.
- `npm run build` (en `apps/desktop`): correcto, con el aviso existente de tamano de bundle.
- `ux-snapshots/latest/spending.png`: revision visual completada.

## Nota

- La herramienta de capturas detectó que el puerto local 1422 ya estaba ocupado, pero reutilizó correctamente el servidor existente y generó las capturas.

## Densidad, estados y tema claro

### Recorridos cubiertos

- Como usuario, quiero cabeceras compactas para llegar antes a la información y acciones de cada módulo.
- Como usuario, quiero que Cuentas no oculte mis saldos y que Planificación no muestre errores internos.
- Como usuario, quiero que Insights explique qué datos faltan y que el tema claro no use blanco puro.

### RED

- Se amplió `test-ui-quality-contracts.ts` para exigir cabeceras compactas, importes sin truncado, una respuesta demo para presupuestos, mensajes accionables en Insights y fondo claro gris cálido.
- La ejecución del contrato falló antes de aplicar los nuevos tokens de tema claro porque `--bg-app` seguía siendo `#f5f5f7`.

### GREEN

- `PageHeader` reduce título, separación y espacio vertical sin perder jerarquía.
- Cuentas conserva los importes completos hasta 100.000 EUR y luego usa una abreviación explícita.
- El demo devuelve una comparativa de presupuestos vacía y Planificación muestra estados entendibles, sin exponer el error de mock.
- El tema claro usa `#EFEEEB` como fondo, con superficies `#F8F7F4`; Ajustes previsualiza los mismos tonos.
- `npm run --prefix tools/ux-snapshot test:ui-quality`: correcto.
- `npm run build` en `apps/desktop`: correcto; persiste el aviso conocido sobre el tamaño del bundle.

| # | Garantía | Prueba | Tipo | Resultado |
|---|---|---|---|---|
| 1 | Las cabeceras son más compactas en escritorio | `test-ui-quality-contracts.ts` | Contrato estático | PASS |
| 2 | Cuentas no trunca saldos con puntos suspensivos | `test-ui-quality-contracts.ts` | Contrato estático | PASS |
| 3 | Planificación puede cargar en demo sin error técnico | `test-ui-quality-contracts.ts` | Contrato estático | PASS |
| 4 | Tema claro y su muestra evitan blanco puro | `test-ui-quality-contracts.ts` | Contrato estático | PASS |
