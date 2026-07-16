# Matriz de cobertura E2E

Los `FLOW-01` a `FLOW-33` son los recorridos principales. Esta matriz completa el catálogo con los límites y fallos que un usuario puede encontrar. Un caso no se considera cubierto hasta que tenga una prueba con resultado `PASS`; diseñarlo no equivale a automatizarlo.

## Objetivo de cobertura

Para cada módulo con escritura deben existir, como mínimo, un camino principal, una validación que no persista datos y una limpieza verificable. Los módulos con proveedores externos deben cubrir además su estado degradado, siempre con fixtures locales.

| Área | Principal | Negativos requeridos | Estado actual |
|---|---:|---:|---|
| Finanzas y planificación | FLOW-01–12 | NEG-01–05 | Diseñados; los negativos están pendientes de automatización. |
| Inversiones | FLOW-13–15 | NEG-06–09 | Diseño y automatización pendientes de fixture/UI determinista. |
| Objetivos, mercados e insights | FLOW-16–24 | NEG-14 | Principales automatizados; reintento pendiente. |
| Patrimonio y seguridad | FLOW-25–26, 30–33 | NEG-15 | Principales automatizados; estado de integridad fallida pendiente. |
| Documentos RAG | FLOW-27 | NEG-10–11 | API disponible; no existe aún una ruta UI de Documentos. |
| Asistente IA | FLOW-28–29 | NEG-12–13 | UI disponible; requiere proveedor fixture local. |

## Criterio de cierre

La cobertura de flujos se considerará completa cuando:

1. Los 33 `FLOW` estén automatizados o tengan una limitación de producto explícita.
2. Todos los casos `NEG` de prioridad `required` tengan ejecución determinista y limpieza comprobada.
3. Todo endpoint que escriba datos tenga una prueba de rechazo sin efectos persistentes.
4. Las rutas UI declaradas en el catálogo existan y muestren estados de carga, vacío y error cuando correspondan.

Los contratos de casos negativos viven en [`negative-cases.yaml`](flows/negative-cases.yaml). Son el backlog verificable; no se ejecutan todavía dentro del runner de `FLOW-01..33`.
