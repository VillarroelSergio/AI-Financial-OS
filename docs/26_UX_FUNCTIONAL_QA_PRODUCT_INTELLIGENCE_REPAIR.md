# 26 — UX Functional QA & Product Intelligence Repair

## Estado

Fase propuesta previa a Packaging & Release.

## Nombre de la fase

**Fase 10.5 — UX Functional QA & Product Intelligence Repair**

## Propósito

Esta fase tiene como objetivo convertir AI Financial OS de una aplicación con módulos funcionales en un producto financiero usable, coherente, fiable y preparado para uso diario antes de empaquetarlo como aplicación instalable.

La fase no busca añadir complejidad innecesaria ni rehacer la aplicación desde cero. Busca revisar y mejorar la experiencia real del usuario, corregir datos engañosos, clarificar módulos confusos, completar flujos incompletos y reforzar la integración de la inteligencia artificial dentro del producto.

## Contexto del producto

AI Financial OS es una aplicación financiera personal local-first. Su diferencial debe estar en:

- Control manual de datos financieros.
- Privacidad local.
- Importaciones revisables.
- Análisis financiero determinista.
- IA local como capa contextual.
- Inversiones, objetivos, planificación, economía y mercado en un único entorno.
- Diseño dark premium.

Antes de Packaging & Release, la app debe sentirse como un producto fiable, no como una colección de módulos técnicos.

## Principio rector

Todas las mejoras deben respetar el flujo de producto:

```txt
Resumen → Explicación → Detalle → Acción
```

Cada pantalla debe responder claramente:

```txt
1. Qué estoy viendo.
2. Qué dato importa.
3. Qué estado tiene ese dato.
4. Qué puedo hacer ahora.
5. Dónde puedo profundizar.
```

## Restricciones globales

Durante esta fase no se debe introducir:

- Automatización bancaria.
- Scraping bancario.
- Scraping de brokers.
- Lectura automática de email.
- Sincronización cloud obligatoria.
- Envío de CSV, capturas, documentos o datos financieros personales a terceros no definidos por el proyecto.
- Recomendaciones financieras vinculantes.
- Cálculos financieros críticos realizados únicamente por un LLM.
- SQL libre generado por IA contra datos personales.

La solución debe respetar la arquitectura, documentación viva, contratos existentes y principios local-first del proyecto.

---

# Plan de ejecución funcional

La fase se debe trabajar de forma incremental y ordenada. Cada subfase debe cerrarse con validación funcional, revisión UX y documentación actualizada antes de avanzar a la siguiente.

Orden recomendado:

```txt
10.5.1 — Product Shell & UI Polish
10.5.2 — Market Cache & Startup Preload
10.5.3 — Economy Data Quality Redesign
10.5.4 — Portfolio Screenshot Import & Portfolio Quality UX
10.5.5 — Transactions Ledger UX Repair
10.5.6 — Spending Visualization Redesign
10.5.7 — Goals Simulation UX Repair
10.5.8 — Smart Planning & Recurring Detection
10.5.9 — Household Bills & Utilities Tracking
10.5.10 — AI Copilot Integration
10.5.11 — Settings & System Readiness
10.5.12 — UX Test Battery & Release Readiness
```

El orden puede ajustarse si el estado real del repositorio lo exige, pero no debe saltarse la validación de los bloqueantes antes de Packaging & Release.

---

# Prioridades

## P0 — Bloqueantes antes de Packaging

Deben resolverse antes de considerar la app lista para empaquetar:

```txt
- Mercados: eliminar errores crudos y asegurar datos cacheados o estados honestos.
- Economía: corregir indicadores repetidos, seed/demo mal presentado y valores incoherentes.
- Inversiones/Reconciliación: corregir fallos de carga y explicar la utilidad de la calidad de cartera.
- Movimientos: eliminar UUID visibles y añadir búsqueda/filtros útiles.
- Importar cartera: aceptar capturas reales o comunicar claramente el alcance soportado.
- Ajustes: mostrar estado real de IA, RAG, backups, seguridad y datos locales.
```

## P1 — Experiencia de producto

Mejoras que hacen que la app se perciba como producto financiero inteligente:

```txt
- Asistente IA contextual integrado.
- Planificación inteligente con detección de recurrentes.
- Objetivos más comprensibles.
- Gastos mejor visualizados.
- Inversiones más claras.
```

## P2 — Evolución funcional

Capacidades de valor adicional que pueden crecer después de los bloqueantes:

```txt
- Control específico de suministros y facturas del hogar.
- Carga futura de facturas por PDF o captura.
- Automatización asistida más avanzada.
- IA con acciones guiadas bajo confirmación.
```

---

# 10.5.1 — Product Shell & UI Polish

## Objetivo

Elevar la percepción visual de la aplicación hacia un centro de mando financiero premium, calmado, claro y accionable.

La UI debe inspirarse en un concepto de **Financial Command Center**, respetando el dark premium actual y mejorando jerarquía, densidad, agrupación visual, estados y acciones principales.

## Problemas actuales

- Algunas pantallas tienen demasiado espacio vacío.
- Algunas secciones parecen técnicas o provisionales.
- Hay formularios inline demasiado grandes.
- Varias pantallas no muestran claramente el estado del dato.
- Las acciones principales no siempre son evidentes.
- Hay tablas grandes con baja capacidad de exploración.

## Requisitos funcionales

Cada módulo principal debe tener:

- Cabecera clara.
- Descripción breve.
- Estado del dato cuando aplique.
- Acción principal visible.
- Acciones secundarias bien jerarquizadas.
- Estados loading, empty, partial, error y success.
- Copy claro en español.
- Badges de estado comprensibles.
- Uso consistente de superficies, cards, tablas y gráficos.

## Resultado esperado

El usuario debe entender cada pantalla en pocos segundos y saber qué acción realizar sin interpretar elementos técnicos.

---

# 10.5.2 — Market Cache & Startup Preload

## Objetivo

Eliminar la sensación de fallo en la sección Mercados y asegurar que siempre se muestre el último dato válido cuando exista.

## Problema

La pantalla de Mercados puede mostrar errores como `Failed to fetch` cuando el usuario accede antes de que los datos estén cargados o cuando un proveedor externo falla.

## Requisitos funcionales

La sección Mercados debe:

- Mostrar el último dato válido disponible cuando exista.
- Diferenciar dato actualizado, dato en caché, dato parcial, dato stale, dato no disponible y error técnico controlado.
- Permitir actualización manual.
- Mostrar fecha, fuente y calidad del dato.
- Evitar errores técnicos crudos como mensaje principal.
- Mantener la pantalla usable si un proveedor externo falla.

## Resultado esperado

El usuario debe ver mensajes como:

```txt
Mostrando últimos datos guardados. Actualizando en segundo plano.
```

O:

```txt
No hay datos de índices todavía. Pulsa Actualizar para cargar los primeros datos.
```

Nunca debe ver `Failed to fetch` como experiencia principal.

---

# 10.5.3 — Economy Data Quality Redesign

## Objetivo

Rediseñar la sección Economía para mostrar datos macro y microeconómicos útiles, fiables y comprensibles para España, Eurozona y Estados Unidos.

## Problema

Se han observado indicadores repetidos o incoherentes, por ejemplo varios indicadores económicos mostrando el mismo valor. Esto daña la confianza del usuario.

## Requisitos funcionales

La sección Economía debe:

- Evitar valores repetidos por fallback incorrecto.
- No mostrar seed/demo como datos reales.
- Mostrar fuente, fecha, unidad y estado de calidad.
- Separar España, Eurozona y Estados Unidos.
- Mostrar solo indicadores útiles para el usuario.
- Explicar por qué cada dato puede importar para sus finanzas personales.
- Marcar datos ausentes, parciales o desactualizados de forma honesta.

## Indicadores mínimos esperados

### España

- IPC general.
- IPC subyacente.
- Paro.
- PIB o crecimiento económico.
- Euríbor 12M.
- Bono España 10Y.

### Eurozona

- Inflación.
- Tipos BCE.
- PIB o crecimiento económico.
- Paro.
- Euro Stoxx 50 o índice europeo relevante.
- EUR/USD.

### Estados Unidos

- CPI.
- Tipos Fed.
- Desempleo.
- PIB o crecimiento económico.
- S&P 500 o Nasdaq 100.
- Treasury 10Y.

## Impacto personal

Debe mantenerse o mejorarse un bloque de impacto personal con lecturas como:

- Inflación vs tasa de ahorro.
- Tipos de interés vs liquidez.
- EUR/USD vs cartera en USD.
- Mercado vs inversiones.

Solo deben mostrarse impactos si los datos usados son válidos y suficientes.

---

# 10.5.4 — Portfolio Screenshot Import & Portfolio Quality UX

## Objetivo

Corregir la experiencia de importación de cartera y hacer comprensible la calidad de la cartera importada.

## Problemas actuales

- La pantalla promete importación desde captura, pero el flujo se basa en pegar texto.
- La revisión/reconciliación de cartera puede fallar o no explicar bien su utilidad.
- El usuario no entiende qué parte de la cartera es fiable, estimada, manual o pendiente de revisión.

## Requisitos funcionales para importación de cartera

El módulo debe ofrecer claramente:

- Importación desde captura real.
- Importación desde texto pegado como fallback.
- Entrada rápida manual.

Para capturas reales debe permitir:

- Cargar una o varias capturas.
- Extraer posiciones cuando sea posible.
- Mostrar una tabla editable de revisión.
- Corregir manualmente todos los campos.
- Validar instrumento.
- Validar precio y FX.
- Calcular coste estimado cuando haya valor actual y rentabilidad.
- Marcar datos capturados, estimados y confirmados.
- No crear holdings sin confirmación explícita.

## Requisitos funcionales para calidad de cartera

La pantalla de calidad/revisión de cartera debe responder:

- Qué parte de la cartera está confirmada.
- Qué parte es estimada.
- Qué parte es manual.
- Qué posiciones requieren revisión.
- Qué posiciones no tienen precio.
- Qué posiciones tienen FX pendiente.
- Qué impide confiar plenamente en el valor total.

## Naming UX

El término “Reconciliación” puede no ser comprensible para usuario final. Debe valorarse un nombre más claro, como:

- Revisión de cartera.
- Calidad de cartera.
- Estado de cartera.

El nombre final debe priorizar comprensión.

---

# 10.5.5 — Transactions Ledger UX Repair

## Objetivo

Convertir Movimientos en una herramienta útil de exploración financiera, no en una tabla técnica masiva.

## Problemas actuales

- Tabla demasiado grande.
- Filtros insuficientes.
- Sin búsqueda por descripción.
- UUID de cuenta visible al usuario.
- Baja utilidad visual.

## Requisitos funcionales

Movimientos debe permitir:

- Buscar por descripción.
- Filtrar por cuenta.
- Filtrar por categoría.
- Filtrar por fecha o periodo.
- Filtrar por tipo.
- Filtrar por importe o rango de importe.
- Ordenar por fecha, importe o categoría.
- Mostrar nombres legibles de cuenta, no IDs internos.
- Detectar o filtrar movimientos sin categoría.
- Crear movimiento.
- Editar movimiento.
- Eliminar movimiento con confirmación.
- Mostrar empty, loading, partial, error y success.

## Preguntas que debe responder

El usuario debe poder encontrar rápidamente:

- Qué gastó en un comercio o descripción concreta.
- Qué movimientos tuvo una cuenta en un periodo.
- Qué gastos superan cierto importe.
- Qué movimientos no tienen categoría.
- Qué ingresos recibió en un mes.

---

# 10.5.6 — Spending Visualization Redesign

## Objetivo

Mejorar la visualización de gastos para que siga siendo clara cuando hay muchas categorías.

## Problema

El gráfico tipo donut pierde legibilidad con demasiadas categorías y genera ruido visual.

## Requisitos funcionales

La pantalla Gastos debe:

- Priorizar ranking de categorías.
- Mostrar cantidades y porcentajes claramente.
- Agrupar categorías pequeñas como “Otros” cuando haya demasiadas.
- Permitir drilldown por categoría.
- Comparar mes actual con mes anterior o media reciente cuando sea útil.
- Evitar visualizaciones saturadas.
- Mantener coherencia visual dark premium.

## Resultado esperado

El usuario debe entender rápidamente:

- Dónde se fue más dinero.
- Qué categoría subió.
- Qué categoría parece anómala.
- Qué movimientos componen cada categoría.

---

# 10.5.7 — Goals Simulation UX Repair

## Objetivo

Hacer que las simulaciones de objetivos sean comprensibles, accionables y confiables.

## Problema

Los escenarios y proyecciones actuales pueden parecer confusos o erróneos para el usuario.

## Requisitos funcionales

Objetivos debe responder claramente:

- Si el usuario va en plazo.
- Cuándo alcanzaría el objetivo.
- Cuánto necesita aportar para llegar en la fecha prevista.
- Qué ocurre si aumenta o reduce la aportación.
- Qué efecto tiene la inflación.
- Qué significa cada escenario.

Debe mostrar:

- Fecha estimada de cumplimiento.
- Aportación mensual necesaria.
- Objetivo ajustado por inflación.
- Estado en plazo / fuera de plazo.
- Escenarios explicados en lenguaje claro.
- Mensaje claro si el objetivo no es alcanzable con la aportación actual.

## Resultado esperado

El usuario debe poder leer mensajes como:

```txt
Con tu aportación actual llegarías en septiembre de 2027.
Para llegar antes de tu fecha objetivo necesitarías aportar aproximadamente X €/mes.
La inflación hace que tu objetivo equivalente sea X € en la fecha prevista.
```

---

# 10.5.8 — Smart Planning & Recurring Detection

## Objetivo

Convertir Planificación en un sistema asistido capaz de detectar patrones recurrentes y mejorar la previsión mensual.

## Problema

La planificación actual depende demasiado de altas manuales de presupuestos y recurrentes.

## Requisitos funcionales

La app debe detectar candidatos recurrentes como:

- Suscripciones mensuales.
- Alquiler o hipoteca.
- Nómina.
- Internet.
- Telefonía.
- Luz.
- Gas.
- Agua.
- Seguros.
- Gimnasio.
- Gastos anuales.
- Gastos semanales.
- Ingresos recurrentes.

Para cada candidato debe mostrar:

- Nombre o descripción probable.
- Importe habitual o rango.
- Frecuencia probable.
- Próxima fecha estimada.
- Nivel de confianza.
- Movimientos usados para detectarlo.

El usuario debe poder:

- Confirmar candidato.
- Editar candidato.
- Ignorar candidato.
- Convertir candidato en recurrente.

## Regla clave

La detección debe ser asistida, no automática. Nada debe convertirse en recurrente sin confirmación explícita del usuario.

---

# 10.5.9 — Household Bills & Utilities Tracking

## Objetivo

Añadir capacidad específica para controlar suministros y facturas del hogar, especialmente gastos variables recurrentes.

## Alcance inicial

La app debe permitir registrar y analizar:

- Luz.
- Gas.
- Agua.
- Internet.
- Telefonía.
- Seguros del hogar.
- Alquiler o hipoteca.
- Comunidad.

## Requisitos funcionales

La app debe permitir:

- Registrar factura manualmente.
- Asociar factura a proveedor.
- Asociar factura a periodo de consumo.
- Registrar importe.
- Registrar categoría.
- Marcar si es recurrente.
- Comparar con meses anteriores.
- Detectar subidas anómalas.
- Estimar próximo recibo.
- Integrar estos datos en planificación mensual.

## Futuro deseable

La fase debe dejar claro el camino futuro para:

- Carga de PDF.
- Captura de factura.
- Extracción local de datos.
- Comparativa de tarifa.
- Registro de consumo kWh o m³.

---

# 10.5.10 — AI Copilot Integration

## Objetivo

Transformar el asistente IA en un copiloto financiero contextual integrado en el producto.

## Problema

El asistente actual se percibe como un chatbot lateral aislado.

## Requisitos funcionales

La IA debe poder:

- Entender en qué módulo está el usuario.
- Recibir contexto relevante de la pantalla actual.
- Explicar métricas visibles.
- Resumir datos del periodo seleccionado.
- Ayudar a interpretar gastos, inversiones, objetivos, planificación, economía e insights.
- Sugerir preguntas útiles según el módulo.
- Mostrar siempre datos utilizados.
- Indicar si faltan datos.
- No inventar cifras.
- No hacer cálculos críticos por sí sola.
- No recomendar compras o ventas de activos.

## Acciones contextuales esperadas

### Gastos

- Explica esta categoría.
- Detecta gastos anómalos.
- Qué gastos parecen recurrentes.

### Movimientos

- Resume mis movimientos del mes.
- Encuentra movimientos sin categoría.
- Detecta posibles duplicados.

### Inversiones

- Revisa mi cartera.
- Explica mi rentabilidad.
- Qué posiciones requieren revisión.

### Planificación

- Detecta posibles suscripciones.
- Propón pagos recurrentes candidatos.
- Explica mi previsión de cashflow.

### Objetivos

- Explícame si voy en plazo.
- Cuánto debería aportar para llegar.
- Compara escenarios.

### Economía y mercados

- Qué indicadores afectan a mi situación.
- Explica el impacto del EUR/USD sobre mi cartera.

## Resultado esperado

La IA debe sentirse como parte del producto, no como una pantalla de chat añadida.

---

# 10.5.11 — Settings & System Readiness

## Objetivo

Convertir Ajustes en el centro de control local del sistema.

## Problema

Ajustes es demasiado limitado para una aplicación que ya incluye IA local, RAG, backups, seguridad, documentos, datos locales y proveedores.

## Requisitos funcionales

Ajustes debe mostrar y permitir gestionar, cuando aplique:

- Idioma.
- Moneda base.
- Tema.
- Estado del backend local.
- Estado del asistente IA.
- Proveedor IA seleccionado.
- Modelo IA seleccionado.
- Estado de Ollama / LM Studio.
- Document Intelligence / RAG.
- Documentos indexados.
- Backups locales.
- Última copia de seguridad.
- Integridad de base de datos.
- Ruta local de datos.
- Política de privacidad local.
- Datos demo/mock.

## Resultado esperado

El usuario debe saber:

- Dónde están sus datos.
- Si la IA está disponible.
- Si hay backups.
- Si la base de datos está íntegra.
- Qué proveedor IA está usando.
- Qué documentos están indexados.

---

# 10.5.12 — UX Test Battery & Release Readiness

## Objetivo

Cerrar la fase con una batería de pruebas funcionales de usuario y un informe de preparación para release.

## Pruebas mínimas por módulo

### Resumen

- Carga con datos reales.
- Carga con datos parciales.
- Top insights visibles.
- Acciones útiles.

### Gastos

- Visualización con pocas categorías.
- Visualización con muchas categorías.
- Drilldown por categoría.
- Comparación mensual.
- Categoría sin movimientos.

### Movimientos

- Buscar por descripción.
- Filtrar por cuenta.
- Filtrar por categoría.
- Filtrar por rango de fechas.
- Filtrar por importe.
- Crear movimiento.
- Editar movimiento.
- Eliminar movimiento con confirmación.

### Cuentas

- Crear cuenta.
- Editar cuenta.
- Eliminar o desactivar cuenta.
- Ver impacto en patrimonio.

### Importación CSV

- Importar Monefy válido.
- Importar CSV inválido.
- Ver preview.
- Confirmar.
- Rollback.

### Inversiones

- Ver cartera con precios actualizados.
- Actualizar precios.
- Ver activos manuales.
- Ver activos sin precio.
- Ver calidad de cartera.
- Ver concentración.

### Importar cartera

- Cargar captura.
- Pegar texto fallback.
- Entrada rápida manual.
- Validar instrumentos ambiguos.
- Confirmar importación.
- Cancelar importación.
- Detectar duplicados.

### Economía

- España.
- Eurozona.
- EEUU.
- Datos disponibles.
- Datos parciales.
- Datos ausentes.
- Impacto personal.

### Mercados

- Primer acceso sin datos.
- Acceso con caché.
- Actualización correcta.
- Proveedor fallando.
- Datos stale.

### Objetivos

- Crear objetivo.
- Simular objetivo.
- Cambiar inflación.
- Cambiar aportación mensual.
- Objetivo alcanzable.
- Objetivo no alcanzable.

### Planificación

- Crear presupuesto.
- Ver gasto vs presupuesto.
- Detectar recurrentes candidatos.
- Confirmar recurrente.
- Ignorar recurrente.
- Ver calendario.
- Ver cashflow.

### Insights

- Ver resumen mensual.
- Filtrar insights.
- Abrir datos utilizados.
- Descartar insight.
- Insight con datos incompletos.

### Asistente IA

- Pregunta general.
- Pregunta contextual desde Gastos.
- Pregunta contextual desde Inversiones.
- Pregunta contextual desde Planificación.
- IA sin provider disponible.
- IA con datos insuficientes.
- Mostrar datos usados.

### RAG

- Subir documento.
- Consultar documento.
- Ver fuentes.
- Documento sin resultados.

### Ajustes

- Cambiar idioma.
- Cambiar moneda base.
- Ver estado IA.
- Ver backups.
- Crear backup.
- Ver integridad de base de datos.
- Ver ruta local de datos.

## Informe final

La fase debe terminar con un informe que indique:

- Listo para Packaging: sí/no.
- Bloqueantes abiertos.
- Mejoras pendientes.
- Riesgos de datos.
- Riesgos UX.
- Snapshots actualizados.
- Pruebas ejecutadas.
- Limitaciones conocidas.

---

# Criterios de aceptación globales

La Fase 10.5 se considera completada cuando:

```txt
1. La app no muestra errores crudos tipo “Failed to fetch” en pantallas principales.
2. La app no muestra UUID internos al usuario.
3. Mercados funciona con datos cacheados o estados honestos.
4. Economía no muestra indicadores repetidos incorrectamente.
5. Revisión de cartera funciona y explica su utilidad.
6. Movimientos permite búsqueda y filtros útiles.
7. Importar cartera acepta capturas reales o comunica claramente el alcance soportado.
8. Gastos es legible con muchas categorías.
9. Objetivos explica escenarios, fechas, aportaciones e inflación.
10. Planificación detecta o propone recurrentes de forma asistida.
11. El asistente IA está integrado contextualmente en módulos clave.
12. Ajustes muestra estado real del sistema local.
13. Todos los módulos tienen loading/empty/partial/error/success.
14. Los datos demo/mock/seed no se presentan como reales.
15. Los datos sensibles no se envían a servicios externos no definidos.
16. La documentación relevante queda actualizada.
17. La batería de pruebas UX queda documentada.
18. Los tests existentes pasan o se documentan fallos previos.
19. Se capturan snapshots UX actualizados de las pantallas principales.
20. La app queda preparada para Packaging & Release o se documentan los bloqueantes pendientes.
```

---

# Documentación a actualizar

Actualizar la documentación viva cuando cambien comportamiento, contratos, naming o reglas de UX.

Documentos relevantes:

```txt
docs/02_ROADMAP.md
docs/03_ARCHITECTURE.md
docs/04_DATA_MODEL.md
docs/06_AI_STRATEGY.md
docs/08_UX_UI_GUIDELINES.md
docs/09_DESIGN_SYSTEM.md
docs/11_API_CONTRACT.md
docs/13_CLAUDE_CODE_GUIDE.md
docs/15_MARKET_PROVIDERS.md
docs/16_INSIGHTS_ENGINE.md
docs/20_PORTFOLIO_IMPORT_ASSISTANT.md
docs/21_GOALS_SIMULATIONS.md
docs/22_PORTFOLIO_RECONCILIATION_ANALYTICS.md
docs/23_BUDGETS_RECURRING_CASHFLOW.md
docs/24_DOCUMENT_INTELLIGENCE_RAG.md
docs/25_HARDENING_SECURITY_BACKUPS.md
```

Este documento debe incorporarse como:

```txt
docs/26_UX_FUNCTIONAL_QA_PRODUCT_INTELLIGENCE_REPAIR.md
```

---

# Entrega esperada al finalizar la fase

El agente debe entregar:

```txt
1. Resumen de problemas corregidos.
2. Módulos modificados.
3. Cambios funcionales percibidos por el usuario.
4. Cambios de datos o calidad de datos.
5. Cambios de IA contextual.
6. Pruebas UX ejecutadas.
7. Snapshots generados.
8. Documentación actualizada.
9. Limitaciones pendientes.
10. Evaluación final: listo/no listo para Packaging & Release.
```

