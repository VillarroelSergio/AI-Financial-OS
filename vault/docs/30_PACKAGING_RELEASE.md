# Packaging y actualizaciones

AI Financial OS se distribuye en Windows con Tauri. El backend FastAPI se compila con PyInstaller en modo `onedir` y Tauri lo incluye como recurso interno. El usuario final no necesita Python, Node ni Rust.

Los datos del usuario no viven dentro de la instalacion. En produccion se guardan en:

```text
%APPDATA%\FinancialAgent\
```

Por eso reinstalar o actualizar la app no debe borrar la base de datos ni la configuracion del usuario.

## Nueva version completa

Usar este flujo cuando se quiere generar una release completa con instaladores `.msi` y `.exe`:

```powershell
.\scripts\build-release.ps1
```

El script hace:

1. Compila el backend con PyInstaller.
2. Copia el backend empaquetado a los recursos de Tauri.
3. Compila frontend, binario Tauri e instaladores.

Salidas:

```text
apps\desktop\src-tauri\target\release\bundle\msi\
apps\desktop\src-tauri\target\release\bundle\nsis\
```

Si ya existe un backend compilado y solo quieres reconstruir Tauri:

```powershell
.\scripts\build-release.ps1 -SkipBackend
```

## Update de la app

Usar este flujo para entregar un unico `.exe` de actualizacion que se instala encima de la version anterior:

```powershell
.\scripts\build-update.ps1 -Version 0.1.1 -Notes "Fix de arranque del backend empaquetado"
```

El script hace:

1. Actualiza la version en los manifests del proyecto.
2. Ejecuta el build completo.
3. Copia el instalador NSIS final a `release\`.
4. Genera un changelog corto.

Salidas:

```text
release\AI-Financial-OS-0.1.1-update.exe
release\CHANGELOG-0.1.1.txt
```

Ese `.exe` es el archivo que se entrega al usuario. Se ejecuta encima de la instalacion actual y conserva los datos en `%APPDATA%\FinancialAgent\`.

Si quieres reutilizar un backend ya compilado:

```powershell
.\scripts\build-update.ps1 -Version 0.1.1 -Notes "Cambio solo de UI" -SkipBackend
```

## Validacion manual

No es obligatorio para generar el instalador, pero antes de entregar una version conviene comprobar:

1. Instalar el `.exe` o `.msi` encima de una version existente.
2. Abrir AI Financial OS desde el acceso del escritorio o menu Inicio.
3. Confirmar que la UI carga.
4. Confirmar que el backend responde.
5. Confirmar que los datos anteriores siguen presentes.

Smoke test disponible:

```powershell
.\scripts\smoke-test.ps1
```

Requiere que el puerto `8010` este libre.

## Cuando usar cada script

| Necesidad | Script |
|---|---|
| Release completa con instaladores finales | `.\scripts\build-release.ps1` |
| Update manual en un unico `.exe` | `.\scripts\build-update.ps1 -Version X.Y.Z -Notes "..."`
| Reconstruir solo Tauri usando backend existente | añadir `-SkipBackend` |

## Nota sobre auto-updater

El auto-updater automatico de Tauri no esta activo. Para activarlo harian falta claves de firma, manifiesto remoto y hosting de releases. Hasta entonces, el update oficial es el `.exe` generado en `release\`.
