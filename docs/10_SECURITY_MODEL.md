# 10 — Security Model

## Nivel inicial

Seguridad básica local, escalable.

La aplicación se ejecuta solo en el ordenador del usuario. No hay sincronización cloud ni automatización bancaria.

## Principios

- Datos personales en local.
- Sin credenciales bancarias.
- Sin scraping.
- Sin subida de archivos financieros a terceros.
- Importación manual.
- Logs sin datos sensibles.
- IA local.

## V1

Incluye:

- SQLite local.
- Carpeta de datos local.
- Configuración local.
- Importaciones manuales.
- Sin cifrado obligatorio.
- Sin autenticación de usuario.

## Ubicación de datos

La app debe permitir configurar o conocer la ruta de datos.

Ejemplo Windows:

```txt
%APPDATA%/AI Financial OS/
  data/
    financial.db
    analytics.duckdb
  imports/
  logs/
  documents/
```

## Logs

No registrar:

- Filas completas de CSV.
- Importes individuales sensibles.
- Prompts con datos financieros.
- Respuestas completas de IA con datos personales.

Sí registrar:

- Estado de importación.
- Número de filas.
- Errores técnicos anonimizados.
- Provider usado.
- Tiempos de ejecución.

## Importaciones

- El usuario selecciona manualmente cada archivo.
- El archivo se procesa localmente.
- Se genera hash del archivo.
- Se guarda resumen de importación.
- No se envía a la IA en V1.

## IA

- Solo local.
- Ollama y LM Studio.
- Los datos enviados al modelo deben ser mínimos y relevantes.
- No enviar toda la base de datos como contexto.
- Usar tools que devuelven datos agregados.

## Datos económicos y mercado

Pueden consultarse online porque no contienen datos personales.

Reglas:

- Cachear localmente.
- Mostrar última actualización.
- Permitir refresh manual.
- No mezclar llamadas de mercado con datos personales.

## Fases futuras

### Seguridad V2

- Cifrado opcional de base de datos.
- Backups manuales.
- Exportación de datos.
- Borrado seguro de importaciones.

### Seguridad V3

- SQLCipher o cifrado a nivel de archivo.
- Claves en Windows Credential Manager.
- Bloqueo por PIN.
- Auditoría local.
- Backups cifrados.

## No permitido

- Guardar credenciales bancarias.
- Implementar scraping bancario.
- Enviar CSV financieros a APIs externas.
- Usar proveedores IA cloud en V1.
- Activar telemetría por defecto.
