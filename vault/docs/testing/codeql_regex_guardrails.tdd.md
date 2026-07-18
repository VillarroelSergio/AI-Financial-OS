---
name: codeql_regex_guardrails_tdd
description: Evidencia TDD de las correcciones para las alertas CodeQL de expresiones regulares en importación de cartera y guardrails de IA.
metadata:
  type: project
---

# Correcciones CodeQL: regex de importación y guardrails

## Garantías

- `POST /api/investments/import/parse-text` rechaza texto de más de 100.000 caracteres con `422`.
- El parseo del formato numérico español `1.234,56` ya no depende de una expresión regular con repetición.
- El sanitizador de respuestas de IA elimina emojis sin usar un rango Unicode dentro de una expresión regular.

## Evidencia TDD

| Etapa | Comando | Resultado |
| --- | --- | --- |
| RED | `uv run pytest app/tests/test_portfolio_import.py app/tests/test_guardrails.py -q` | 3 fallos esperados: dependencia de `re.match`, entrada sobredimensionada aceptada y emoji eliminado. |
| RED (política de emoji) | `uv run pytest app/tests/test_portfolio_import.py app/tests/test_guardrails.py -q` | 1 fallo esperado: el sanitizador conservaba el emoji. |
| GREEN | `uv run pytest app/tests/test_portfolio_import.py app/tests/test_guardrails.py -q` | 35 pruebas correctas. |
| Lint | `uv run ruff check app/modules/investments/portfolio_import_service.py app/modules/investments/portfolio_import_routes.py app/modules/ai/prompts/guardrails.py app/tests/test_portfolio_import.py app/tests/test_guardrails.py` | Correcto. |
| Autochequeo | `uv run python -m app.modules.ai.prompts.guardrails` | `guardrails self-check ok`. |

## Cobertura y límites

El entorno actual de Pytest no tiene habilitado `pytest-cov` (`pytest --help` no expone opciones `--cov`), por lo que no se informa una cifra de cobertura. Las pruebas focalizadas cubren el límite HTTP, el formato español de miles y la eliminación de emojis en el sanitizador.

**Relacionadas:** [[MOC - Testing]] · [[ESTADO]] · [[10_SECURITY_MODEL]]

Tags: #testing #tdd #security #codeql
