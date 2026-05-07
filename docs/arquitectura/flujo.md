# Flujo de datos

Paso a paso de lo que ocurre en cada fase del pipeline.

## Fase 1: Carga de teletipos

```
Archivo CSV/JSON               SQLite
┌─────────────────┐            ┌──────────────┐
│ id: EP-001      │            │ teletipos    │
│ titular: "..."  │──INSERT───→│              │
│ cuerpo: "..."   │  OR IGNORE │ (deduplica   │
│ fecha: "..."    │            │  por id)     │
└─────────────────┘            └──────────────┘
```

- Se ejecuta manualmente o desde un sistema externo
- `INSERT OR IGNORE`: si el id ya existe, no se sobreescribe
- Formatos: CSV (con cabecera) o JSON (array de objetos)

## Fase 2: Ingesta RSS

```
Para cada medio en feeds.yaml:
  Para cada feed (seccion):
    ┌──────────────────┐
    │ feedparser.parse  │
    │ (URL del RSS)     │
    └────────┬─────────┘
             │
             ▼
    Para cada entry del feed:
    ┌──────────────────┐
    │ Extraer:         │
    │  - title         │
    │  - link          │
    │  - summary       │
    │  - published     │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ INSERT articulo  │
    │ (URL es UNIQUE:  │
    │  ignora dupes)   │
    └──────────────────┘
```

- `feedparser` maneja XML/RSS/Atom transparentemente
- HTML en summaries se limpia con regex (`_strip_html`)
- Fechas se parsean desde `published_parsed` o `updated_parsed`
- Articulos duplicados (misma URL) se ignoran automaticamente

## Fase 3: Matching

```
Articulos sin match previo
         │
         ▼
Para cada articulo:
  ┌────────────────────────────────┐
  │ 1. Buscar teletipos en        │
  │    ventana ±48h de la fecha   │
  │    del articulo               │
  └────────────┬───────────────────┘
               │
               ▼
  ┌────────────────────────────────┐
  │ 2. Para cada teletipo:        │
  │    score = partial_ratio(     │
  │      normalizar(art.titular), │
  │      normalizar(tel.titular)  │
  │    )                          │
  └────────────┬───────────────────┘
               │
               ▼
  ┌────────────────────────────────┐
  │ 3. Si score >= 80:            │
  │    → Es un MATCH              │
  │    → Calcular score_cuerpo    │
  │      (informativo)            │
  │    → INSERT en matches        │
  └────────────────────────────────┘
```

**Optimizaciones de rendimiento:**
- Solo procesa articulos que aun no tienen match (LEFT JOIN WHERE NULL)
- La ventana temporal reduce los candidatos drasticamente
- `normalizar()` es lowercase + strip (barato)

**Por que `partial_ratio` y no `ratio`:**
`partial_ratio` busca la mejor subcadena. Si el teletipo dice "Gobierno aprueba plan de vivienda" y el articulo dice "El Gobierno aprueba el plan de vivienda para jovenes menores de 35", partial_ratio da ~95 mientras ratio daria ~70.

## Fase 3.5: Scraping de refuerzo (pendiente)

```
Articulos SIN match tras Fase 3
         │
         ▼
Para cada articulo sin match:
  ┌────────────────────────────────┐
  │ 1. Scrapling abre la URL      │
  │    del articulo                │
  │    Fetcher.get(articulo.url)   │
  └────────────┬───────────────────┘
               │
               ▼
  ┌────────────────────────────────┐
  │ 2. Extraer:                   │
  │    - Texto completo           │
  │    - Campo autor/fuente       │
  └────────────┬───────────────────┘
               │
               ▼
  ┌────────────────────────────────┐
  │ 3a. Si autor contiene         │
  │     "Europa Press"            │
  │     → MATCH DIRECTO           │
  │     (metodo='fuente')         │
  ├────────────────────────────────┤
  │ 3b. Si no:                    │
  │     fuzzy match texto         │
  │     completo vs cuerpo        │
  │     teletipo                  │
  │     → si score >= umbral      │
  │     → MATCH                   │
  │     (metodo='scraping_fuzzy') │
  └────────────────────────────────┘
```

**Por que solo articulos sin match:**
- Si ya matcheo por titular RSS (Fase 3), no hay razon para scrapear
- Reduce el volumen de requests de ~1000 a ~100-150 por ciclo
- Evita rate limiting y bloqueos

**Estado:** Pendiente de implementar. feedparser (Fase 2) + fuzzy matching (Fase 3) = flujo actual del MVP.

## Fase 4: Reporte

```
SELECT matches + teletipos + articulos
         │
         ▼
  ┌──────────────────┐
  │ Formato tabla    │──→ Rich table (terminal)
  │ Formato CSV      │──→ stdout (pipeable)
  │ Formato JSON     │──→ stdout (para APIs)
  └──────────────────┘
```
