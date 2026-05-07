# Arquitectura

## Vision general

El sistema tiene 5 componentes con un pipeline de 2 pases:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           EP Trazabilidad                                │
│                                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐           │
│  │  CARGA   │    │ INGESTA  │    │ PASE 1   │    │ REPORTE  │           │
│  │          │    │          │    │          │    │          │           │
│  │ CSV/JSON │    │feedparser│    │ RapidFuzz│    │ table    │           │
│  │ → SQLite │    │ RSS feeds│    │ titular  │    │ csv/json │           │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘           │
│       │               │               │               │                 │
│       │               │          ┌────┴─────┐         │                 │
│       │               │          │ sin match│         │                 │
│       │               │          └────┬─────┘         │                 │
│       │               │               │               │                 │
│       │          ┌────┴─────┐    ┌────┴─────┐         │                 │
│       │          │ SCRAPING │    │ PASE 2   │         │                 │
│       │          │          │    │          │         │                 │
│       │          │ Scrapling│───→│ cuerpo + │         │                 │
│       │          │ URLs     │    │ fuente   │         │                 │
│       │          └──────────┘    └────┬─────┘         │                 │
│       │                               │               │                 │
│       ▼               ▼               ▼               ▼                 │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                       SQLite (data/)                              │   │
│  │  teletipos │ articulos (+ autor, cuerpo_completo) │ matches       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

## Componentes

### 1. Carga de teletipos (`src/cli.py` → `cmd_load_teletipos`)

Importa los teletipos de la agencia a la base de datos local. Acepta CSV o JSON.

**Input:** archivo con campos `id, titular, cuerpo, fecha_emision, categoria`
**Output:** registros en tabla `teletipos`

### 2. Ingesta RSS (`src/ingesta/rss.py` — feedparser)

Recoge articulos de los medios cliente parseando sus feeds RSS. Rapido y ligero: ~1000 articulos en segundos.

**Input:** lista de feeds definidos en `config/feeds.yaml`
**Output:** registros en tabla `articulos`

**Que extrae de cada entrada RSS:**
- `titular` — el titular del articulo
- `resumen` — summary/description del feed (HTML limpiado)
- `url` — link al articulo original
- `fecha_publicacion` — published_parsed o updated_parsed
- `medio` + `seccion` — de la config

### 3. Pase 1: Matching por titular (`src/matching/matcher.py` → `run`)

Compara titular del articulo vs titular del teletipo con `fuzz.partial_ratio`.

**Algoritmo:**
1. Para cada articulo sin match previo
2. Buscar teletipos emitidos en ±48h de la fecha del articulo
3. Si `partial_ratio(titular_articulo, titular_teletipo) >= 80` → match
4. Guardar con `metodo='fuzzy'`

Cubre ~85-90% de los casos. Los medios suelen mantener titulares parecidos.

### 4. Scraping con Scrapling (`src/scraping/scraper.py`)

Para articulos que NO matchearon en el pase 1: abre la URL real con Scrapling y extrae contenido completo.

**Que extrae:**
- `autor` — meta tags o elementos HTML del articulo
- `cuerpo_completo` — todos los parrafos del articulo (texto limpio)
- `fuente_detectada` — si el texto o autor contienen keywords de la agencia

**Velocidad:** ~1 articulo/segundo (con delay configurable para no saturar).

### 5. Pase 2: Deep matching (`src/matching/matcher.py` → `run_deep`)

Usa los datos de scraping para detectar matches que el pase 1 no pudo:

**Tres vias de deteccion:**

a) **Fuente directa:** si el campo autor contiene "Europa Press" → match automatico con todos los teletipos en ventana. `metodo='fuente'`

b) **Match por cuerpo:** `partial_ratio(cuerpo_teletipo, cuerpo_articulo) >= 70` → detecta cuando el texto del teletipo aparece literal dentro del articulo. `metodo='scraping_fuzzy'`

c) **Match por titular relajado:** si el cuerpo matchea, un titular con score mas bajo tambien vale.

### 6. Reporte (`src/cli.py` → `cmd_report`)

Genera la salida en tabla (Rich), CSV o JSON. Incluye el campo `metodo` para saber como se detecto cada match.

## Por que dos pases

| | Pase 1 (titular) | Pase 2 (scraping) |
|---|---|---|
| Velocidad | ~1000 arts/seg | ~1 art/seg |
| Cobertura | ~85-90% | +5-10% adicional |
| Requiere HTTP | No (datos ya en DB) | Si (abre cada URL) |
| Riesgo de bloqueo | Ninguno | Bajo (con delay) |

El pase 2 solo se ejecuta sobre articulos sin match (~10-15% del total), no sobre todos. Esto minimiza requests y riesgo de bloqueo.

## Documentos relacionados

- [Esquema de datos](esquema.md) — Tablas SQLite, indices, relaciones
- [Flujo de datos](flujo.md) — Pipeline detallado paso a paso
