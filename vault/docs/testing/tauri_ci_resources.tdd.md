# Tauri CI — recursos en checkout limpio

## Origen y alcance

Las PR #39 y #40 fallaron en `Tauri · Cargo check`. La configuración declara
`binaries/backend` como recurso, pero el directorio quedaba vacío y no llegaba al checkout
limpio de GitHub Actions.

## Evidencia RED / GREEN

| Garantía | Evidencia | Resultado |
|---|---|---|
| El recurso declarado existe tras clonar el repositorio | RED remoto: `resource path \`binaries\\backend\` doesn't exist` | Fallo reproducido en ambos PR |
| El directorio se conserva sin versionar el binario de release | `apps/desktop/src-tauri/binaries/backend/.gitkeep`, permitido por `.gitignore` | Aplicado |
| Tauri valida la configuración con el recurso presente | `cargo check --locked` | PASS (9,19 s) |

No procede cobertura: el cambio es un marcador de recurso, sin lógica ejecutable.
