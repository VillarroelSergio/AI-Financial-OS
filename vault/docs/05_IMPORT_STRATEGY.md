# 05 — Import Strategy

## Decisión principal

Toda importación de datos personales será manual por seguridad. No se implementará automatización bancaria, scraping ni lectura de email.

## Objetivo V1

Permitir al usuario importar archivos CSV desde Monefy y otros proveedores mediante un flujo seguro, revisable y reversible.

## Flujo UX

```txt
Seleccionar fuente
 → Seleccionar archivo
 → Detectar formato
 → Mostrar vista previa
 → Validar columnas
 → Normalizar datos
 → Detectar duplicados
 → Confirmar importación
 → Guardar en SQLite
 → Actualizar dashboards
```

## Fuentes iniciales

### V1

- Monefy CSV.
- CSV genérico.

### Futuro

- BBVA CSV.
- Revolut CSV.
- Trade Republic CSV/PDF.
- Finizens CSV/PDF/manual.

## Monefy CSV detectado

Archivo de ejemplo: `monefy-2026-06-22_04-51-25.csv`.

Columnas detectadas:

```txt
date
account
category
amount
currency
converted amount
currency.1
description
```

Características observadas:

- Codificación: UTF-8 con BOM.
- Separador: coma.
- Formato de fecha observado: `D/M/YYYY`.
- Cuenta observada: `Efectivo`.
- Importe positivo para ingresos.
- Importe negativo para gastos.
- Moneda del archivo: USD en el ejemplo, aunque la app debe soportar EUR y otras divisas.
- Descripción puede estar vacía.
- El nombre duplicado de columna `currency` puede aparecer como `currency.1` al leer con pandas.

## Mapeo Monefy → Transaction

```txt
Monefy.date              → Transaction.date
Monefy.account           → Account.name
Monefy.category          → Category.name
Monefy.amount            → Transaction.amount
Monefy.currency          → Transaction.currency
Monefy.converted amount  → Transaction.converted_amount
Monefy.currency.1        → Transaction.converted_currency
Monefy.description       → Transaction.description
```

## Normalización

### Fecha

- Aceptar `D/M/YYYY` y `DD/MM/YYYY`.
- Convertir a ISO `YYYY-MM-DD`.
- Si hay ambigüedad, pedir confirmación en la UI.

### Importes

- Mantener signo original.
- Clasificar:
  - `amount > 0`: ingreso.
  - `amount < 0`: gasto.
  - `amount = 0`: inválido salvo casos especiales.

### Categorías

- Si la categoría no existe, crearla como categoría de usuario.
- Permitir editar categoría antes de confirmar.
- Guardar categoría original importada.

### Cuentas

- Si la cuenta no existe, proponer crearla.
- En Monefy, `Efectivo` puede mapearse a una cuenta tipo `cash`.

## CSV genérico

El importador genérico debe permitir mapear columnas manualmente:

Campos mínimos:

- Fecha.
- Importe.

Campos recomendados:

- Descripción.
- Categoría.
- Cuenta.
- Moneda.

## Detección de duplicados

### Estrategia V1

Calcular hash simple por:

```txt
source_name + date + amount + normalized_description + category
```

### Estrategia posterior

Scoring por:

- Fecha exacta o cercana.
- Mismo importe.
- Descripción similar.
- Misma categoría.
- Misma cuenta.
- Mismo archivo de origen.

## Historial y rollback

Cada importación crea un `ImportBatch`. El usuario debe poder:

- Ver importaciones anteriores.
- Ver cuántas filas se importaron.
- Ver errores.
- Revertir una importación completa.

## Validaciones

Una fila es inválida si:

- No tiene fecha.
- No tiene importe.
- El importe no es numérico.
- La fecha no se puede parsear.
- La moneda es inválida.

Una fila es advertencia si:

- No tiene descripción.
- No tiene categoría.
- La categoría es nueva.
- Posible duplicado.

## UI del Import Center

Pantallas:

1. Source Selection.
2. File Upload.
3. Mapping.
4. Preview.
5. Validation Results.
6. Confirm Import.
7. Import Summary.

## Reglas de seguridad

- No subir archivos a servicios externos.
- No enviar contenido financiero a la IA durante importación en V1.
- No registrar filas completas en logs.
- Guardar solo nombre de archivo, hash y resumen.

## Testing

Crear tests para:

- Parseo de Monefy.
- Fechas españolas.
- Importes negativos.
- Descripciones vacías.
- Categorías nuevas.
- Duplicados exactos.
- Rollback.
