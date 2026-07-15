# 25 - Hardening, Security & Backups

La Fase 10 anade una capa minima de operacion diaria: backups, verificacion de integridad y estado de seguridad local antes del empaquetado.

## Capacidades

- Backup local de la base SQLite en `data/backups`.
- Listado de backups disponibles.
- Validacion de integridad SQLite con `PRAGMA integrity_check`.
- Verificacion de conectividad SQLAlchemy.
- Comprobacion de tablas criticas.
- Estado de hardening con ruta de base de datos, entorno, preparacion para cifrado y politica demo.

## API

- `GET /api/security/status`
- `GET /api/security/backups`
- `POST /api/security/backups`
- `GET /api/security/integrity`

## UI en Ajustes

La pantalla Ajustes consume estos endpoints y muestra:

- Ruta local de base de datos con accion de copiar.
- Estado de integridad y numero de tablas verificadas.
- Numero de backups disponibles.
- Ultima copia local con fecha y tamano.
- Accion para crear un backup manual desde la UI.
- Politica local de datos demo/mock.

## Politicas

- Los backups se guardan localmente y no salen del dispositivo.
- Los logs y errores no deben incluir importes, descripciones completas ni datos financieros sensibles.
- Los datos demo deben estar marcados y excluidos de totales reales.
- El cifrado queda preparado a nivel de contrato.
