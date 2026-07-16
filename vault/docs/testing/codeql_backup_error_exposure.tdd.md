---
name: codeql_backup_error_exposure_tdd
description: Evidencia TDD de la corrección de exposición de detalles internos en el endpoint de copias de seguridad.
metadata:
  type: project
---

# Corrección CodeQL: detalles internos en copias de seguridad

## Garantía

Cuando no existe la base de datos de origen, `POST /api/security/backups` devuelve un error 404 genérico y no expone rutas ni el mensaje interno de la excepción. El detalle se conserva en el registro del servidor.

| Etapa | Comando | Resultado |
| --- | --- | --- |
| RED | `uv run pytest app/tests/test_security.py -q` | Falló: la respuesta incluía `/srv/private-data/financial.db`. |
| GREEN | `uv run pytest app/tests/test_security.py -q` | 3 pruebas correctas. |
| Lint | `uv run ruff check app/modules/security/routes.py app/tests/test_security.py` | Correcto. |

La ejecución completa de Pytest quedó bloqueada por permisos de Windows al crear directorios temporales; no guarda relación con esta corrección. La prueba específica cubre el comportamiento de seguridad afectado.

**Relacionadas:** [[MOC - Testing]] · [[ESTADO]]

Tags: #testing #tdd #security #codeql
