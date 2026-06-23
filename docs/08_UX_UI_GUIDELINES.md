# 08 — UX/UI Guidelines

## Dirección visual

La aplicación debe sentirse como un producto financiero premium, moderno y tranquilo.

Inspiración:

- Linear: claridad, jerarquía y navegación lateral.
- Arc: suavidad visual.
- Raycast: acciones rápidas.
- Notion: simplicidad y bloques.
- Apple Health/Wallet: datos personales presentados con calma.

## Principio UX principal

Resumen → Explicación → Detalle → Acción.

## Tono visual

- Dark premium.
- Superficies suaves.
- Alto contraste pero no agresivo.
- Datos respirados.
- Pocas métricas por pantalla.
- Gráficas simples.
- IA integrada de forma contextual.

## Navegación principal

```txt
Overview
Spending
Investments
Goals
Economy
Insights
Imports
Settings
```

Se puede agrupar en sidebar:

```txt
Core
- Overview
- Spending
- Investments
- Goals

Intelligence
- Economy
- Insights

Data
- Imports
- Accounts
- Transactions

System
- Settings
```

## Overview

Debe responder: “¿Cómo estoy financieramente ahora mismo?”

Elementos:

- Patrimonio neto.
- Liquidez.
- Inversiones.
- Gasto mensual.
- Ahorro mensual.
- Evolución.
- Objetivo principal.
- Insight destacado.

## Spending

Debe responder: “¿Dónde se está yendo mi dinero?”

Elementos:

- Gasto del mes.
- Ingresos del mes.
- Tasa de ahorro.
- Gastos por categoría.
- Evolución mensual.
- Movimientos recientes.
- Posibles anomalías.

## Investments

Debe responder: “¿Cómo evolucionan mis inversiones?”

Elementos:

- Valor total.
- Aportado.
- Rentabilidad.
- Distribución.
- Activos principales.
- Comparativa con índices.

## Economy

Debe responder: “¿Qué contexto económico importa ahora?”

Elementos:

- Snapshot España.
- Snapshot Eurozona.
- Snapshot EEUU.
- Tipos.
- Inflación.
- Mercado.
- Impacto personal.

## Imports

Debe ser claro y seguro.

Flujo:

```txt
Fuente → Archivo → Preview → Validación → Confirmación → Resumen
```

## IA

La IA no debe ocupar la pantalla principal.

Patrones:

- Insight Cards.
- Botón “Preguntar sobre estos datos”.
- Panel lateral derecho.
- Preguntas sugeridas.

## Reglas anti-sobrecarga

- Máximo 4 métricas principales por pantalla.
- Máximo 1 gráfica grande por sección visible.
- Evitar tablas como vista principal.
- No usar más de 5 colores funcionales.
- No mostrar decimales innecesarios.
- No mostrar datos macro sin explicar su relevancia.
- No mezclar finanzas personales y macro en la misma card salvo en “Impacto personal”.

## Empty states

Los estados vacíos deben guiar al usuario.

Ejemplo:

```txt
Todavía no hay movimientos
Importa tu primer CSV de Monefy para empezar a visualizar tus gastos.
[Importar CSV]
```

## Copywriting

Tono:

- Claro.
- Prudente.
- Cercano.
- Sin alarmismo.
- Sin prometer resultados.

Ejemplos:

- “Tu ahorro está por debajo de tu media.”
- “Este gasto parece superior a lo habitual.”
- “Faltan datos para calcular esta métrica.”
- “Última actualización: hace 2 horas.”

Evitar:

- “Mala situación”.
- “Compra ahora”.
- “Alerta crítica” salvo errores reales.
- “Garantizado”.
