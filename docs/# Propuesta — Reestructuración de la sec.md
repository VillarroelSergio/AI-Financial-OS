# Propuesta — Reestructuración de la sección Economía

**Fecha:** 2026-07-06
**Estado:** Borrador para revisión
**Base:** Inventario Tabla A (78 indicadores mostrados) / Tabla B (17 de 35 proveedores sin uso) + `07_ECONOMIC_INTELLIGENCE.md` + `PLAN_MEJORA_ECONOMIA.md`
**Criterio rector:** un dato entra en Economía solo si puede alimentar una comparativa de impacto personal o una decisión financiera del usuario. Lo demás es portal macro, que la spec de producto excluye explícitamente.

---

## 1. Lectura del estado actual (Tabla A)

**España (19)** ha quedado fuerte tras la ampliación INE: los subgrupos de IPC (alimentación, vivienda, transporte, restauración), IPV, hipotecas, coste laboral y comercio minorista son exactamente el tipo de dato que permite pasar de "la inflación es X%" a "la inflación de *tu* cesta es Y%". Es la mejor materia prima nueva que tenemos y todavía no la estamos explotando en impacto personal.

**Eurozona (7) y EEUU (11)** están bien curados; no necesitan crecer.

**Riesgo detectado:** con 37 indicadores de economía ya rozamos densidad de portal. El problema a resolver no es "más datos" sino **estructura**: agrupar por temas que respondan preguntas del usuario, con impacto personal arriba. La ampliación de datos debe ser quirúrgica.

**Fix menor:** `policy_rate` cae en "Otros" por no estar en `_THEME_BY_SUBCATEGORY` — 1 línea. (Con ECO-6, este mapeo entero migra al backend y esta clase de bug desaparece.)

---

## 2. Triaje de la Tabla B

### 2.1 Incorporar a Economía (pasan el filtro de impacto personal)

| Proveedor | Dato | Por qué pasa el filtro | Comparativa personal que habilita |
|---|---|---|---|
| `tesoro` | Subastas: rendimiento de Letras 3/6/9/12M (y Bonos/Obligaciones) | Las Letras son **el** producto de ahorro minorista de referencia en España; dato directamente accionable | "Letras 12M rinden X% vs tu cuenta remunerada al Y%" — conecta además con el calculador de intereses de cuentas de ahorro del plan de Inversiones (tipo DFR BCE) |
| `ree` | Precio medio diario del pool eléctrico (y demanda) | La luz es una categoría de gasto real del usuario; dato diario con alta saliencia | "El pool subió 18% este mes; tu gasto en suministros subió 12%" — cruce con categoría de gasto |
| `seguridad_social` | Afiliación media mensual | Termómetro de empleo España más fresco que la EPA trimestral | Contexto del bloque Empleo; sin comparativa personal directa → **tier 2, opcional** |

### 2.2 Redirigir a otros módulos (valor real, sitio equivocado)

| Proveedor | Destino correcto | Motivo |
|---|---|---|
| `openfigi`, `fmp` | **Inversiones** — asset resolution / validación de instrumento del Portfolio Import (spec 10.5.4) | Identificadores y fundamentales sirven al holding, no al contexto macro |
| `cnmv`, `edgar` | **Inversiones** (folletos/filings de posiciones del usuario) o **RAG** | Documentación por instrumento, no indicador económico |
| `eur_lex` | **RAG / Noticias** como mucho | Normativa no es un indicador; podría alimentar noticias regulatorias curadas, prioridad baja |

### 2.3 No incorporar a UI (portal macro / sin ruta a impacto personal)

`bea`, `census`, `imf`, `bis`, `un_data`, `european_commission`, `twelvedata`, `aemet`, `agencia_tributaria`.

- Componentes del PIB US, demografía, WEO, estadísticas BIS/ONU: cobertura exhaustiva que la spec descarta. Si algún día aportan, que sea vía **AI datasheet** (contexto para el asistente), nunca como cards en la UI.
- `aemet`: sin vínculo financiero personal defendible. Descartar para Economía.
- `agencia_tributaria` (recaudación): agregado sin lectura personal. Descartar.

**Recomendación de higiene:** los adapters de 2.3 que no consuma ni la UI ni el datasheet son código sin consumidor — candidatos a marcarse como dormant o retirarse en la línea del audit de código muerto, para no mantener superficie sin uso.

### 2.4 Series INE adicionales (de las "miles" disponibles): solo dos con retorno claro

1. **IPC por CCAA** — permite mostrar la inflación de la comunidad del usuario junto a la nacional. Personalización real, coste bajo (misma API ya integrada). Requiere un ajuste de configuración local ("mi comunidad"), nunca inferencia automática.
2. **Salarios ETCL por sector** — solo si el usuario declara su sector en configuración; si no, no se muestra. Tier 2.

El resto (turismo, población, comercio exterior) no pasa el filtro.

---

## 3. Estructura propuesta de la sección Economía

Tres niveles, de lo personal a lo contextual. El agrupado temático se resuelve en **backend** (subcategorías del catálogo → temas), no en `EconomyPage.tsx` (alineado con ECO-6).

### Nivel 1 — «Tu economía» (arriba, protagonista)

Comparativas deterministas, solo si hay dato válido (regla vigente de `no_data`). A las existentes se suman las que los datos nuevos habilitan:

| Comparativa | Datos usados | Estado |
|---|---|---|
| **Inflación de tu cesta** vs IPC general | IPC subgrupos × gasto por categoría del usuario (ponderado por su peso real de gasto) | **Nueva — la estrella de la propuesta.** Ya tenemos ambos lados del cruce |
| Euríbor vs tu hipoteca | Euríbor 12M × cuota/deuda hipotecaria | Existente, se mantiene |
| **Letras vs tu ahorro** | Rendimiento subasta 12M × tipo de tus cuentas remuneradas | **Nueva** (requiere `tesoro`) |
| **Luz: pool vs tu factura** | Precio pool mensual × categoría suministros | **Nueva** (requiere `ree`) |
| Inflación vs tasa de ahorro | Existente | Se mantiene |
| EUR/USD vs cartera USD, mercado vs inversiones | Existente | Se mantiene |

Nota: estas comparativas nuevas se implementan sobre la **tabla de definiciones** de ECO-4 (no sobre el `impact.py` monolítico actual). Añadirlas antes del refactor sería copy-paste de 30 líneas cada una — mala idea.

### Nivel 2 — España por temas (respondiendo preguntas, no listando series)

| Tema | Pregunta que responde | Indicadores |
|---|---|---|
| **Precios y consumo** | ¿Qué se encarece? | IPC general/subyacente, subgrupos, comercio minorista, confianza consumidor |
| **Vivienda** | ¿Cómo está el mercado si compro/vendo/hipoteco? | IPV, hipotecas nº + importe, Euríbor 12M |
| **Ahorro y tipos** | ¿Qué me renta el dinero parado? | Euríbor 3M/12M, tipo BCE, **Letras 3/6/12M** (nuevo), bono ES 10Y |
| **Empleo y salarios** | ¿Cómo está el mercado laboral? | Desempleo EPA, coste laboral, *(afiliación SS — tier 2)* |
| **Energía** | ¿Sube la luz? | **Pool REE** (nuevo); Brent/gas quedan en Mercados·Materias primas con cross-link, sin duplicar |
| **Actividad y cuentas públicas** | ¿Cómo va el país? | PIB, producción industrial, déficit, deuda |

Cada tema: 3-6 indicadores máximo, colapsable, con fuente/fecha/quality como hasta ahora. Si `IPC por CCAA` se aprueba, se muestra dentro de "Precios y consumo" junto al nacional cuando el usuario haya configurado su comunidad.

### Nivel 3 — Eurozona y EEUU (compactos, sin crecer)

Como ahora, con dos retoques: `policy_rate` asignado a su tema, y misma estructura temática ligera (Precios / Tipos / Actividad) para consistencia visual con España.

---

## 4. Encaje en el plan ECO (secuencia)

La regla es **no ampliar el catálogo antes de ECO-1**: cada indicador nuevo bajo el contrato laxo actual es superficie extra para la contaminación que estamos intentando cerrar. Encaje propuesto:

| Cuándo | Qué |
|---|---|
| ECO-1 (contrato estricto) | La ampliación INE ya hecha (sin commitear) se revisa contra el contrato nuevo: allowlist explícita en `ine.py`, `fetch(catalog_item_id)` por serie. Se commitea junto con ECO-1 o inmediatamente después |
| ECO-2 (auditoría catálogo) | Se añade aquí la parte de alta de esta propuesta: **ECO-2b — Alta de `tesoro` y `ree`** como items de catálogo con allowlist, frecuencia real (subastas ≈ semanal/quincenal; pool diario) y QualityEngine estándar. Los adapters existen; el trabajo es cablear catálogo + normalización |
| ECO-4 (tabla de comparativas) | Las 3 comparativas nuevas del Nivel 1 se dan de alta como filas de la tabla de definiciones, con sus umbrales en `constants.py`. La de "inflación de tu cesta" usa el mapeo explícito categoría↔subgrupo IPC (el mismo endurecimiento de matching ya previsto en ECO-4.4) |
| ECO-6 (UI) | Se implementa la estructura de 3 niveles con el agrupado temático resuelto en backend. `_THEME_BY_SUBCATEGORY` y el fix de `policy_rate` desaparecen absorbidos por esto |
| Post-plan (tier 2, opcional) | Afiliación SS, IPC por CCAA, salarios por sector — solo tras validar que los tier 1 aportan y que la sección no se ha densificado de más |

Coste incremental estimado sobre el plan: **+2-3 días** (ECO-2b ~1 día, comparativas nuevas ~0.5-1 día dentro de ECO-4, estructura temática ya estaba contemplada en ECO-6 y se concreta con esta propuesta).

---

## 5. Qué NO hace esta propuesta (explícito)

- No convierte Economía en portal: de 17 proveedores ociosos entran **2** (tesoro, ree), 4-6 se redirigen a Inversiones/RAG y ~9 se descartan de UI.
- No añade datos sin comparativa o decisión asociada: cada indicador nuevo del Nivel 2 pertenece a un tema con pregunta de usuario.
- No infiere datos personales: comunidad autónoma y sector son configuración explícita del usuario o no se muestran.
- No toca la ingesta antes del contrato estricto.

---

## 6. Decisiones que necesito de ti

1. **¿Apruebas el corte del triaje?** En particular: `seguridad_social` como tier 2 (yo lo dejaría fuera del primer paso), y el descarte total de `aemet`/`agencia_tributaria` de la UI.
2. **Comparativa "inflación de tu cesta":** ¿ponderamos por el peso real de gasto del usuario en cada subgrupo (más preciso, más lógica) o mostramos subgrupo a subgrupo la pareja IPC vs variación de tu gasto (más simple, más transparente)? Mi recomendación: empezar por la simple y evolucionar.
3. **`tesoro`:** ¿solo Letras (foco ahorro minorista) o también Bonos/Obligaciones en subasta? Recomiendo solo Letras en UI; el resto ya está cubierto por el bono 10Y de mercado secundario.
4. **La ampliación INE sin commitear:** ¿la revisamos contra el contrato de ECO-1 antes de commitear, o la commiteas ya y la adaptamos en ECO-1? Recomiendo lo primero para no consolidar adapters con el contrato viejo.