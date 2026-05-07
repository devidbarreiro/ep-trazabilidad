# Esquema de datos

Base de datos SQLite con 3 tablas. Archivo: `data/trazabilidad.db`.

## Diagrama de relaciones

```
teletipos                    articulos
┌──────────────────┐         ┌──────────────────┐
│ id (PK, TEXT)    │         │ id (PK, AUTO)    │
│ titular          │         │ medio            │
│ cuerpo           │         │ seccion          │
│ fecha_emision    │         │ titular          │
│ categoria        │         │ resumen          │
└────────┬─────────┘         │ url (UNIQUE)     │
         │                   │ fecha_publicacion│
         │                   │ fecha_ingesta    │
         │                   │ autor  (scraping)│
         │                   │ cuerpo_completo  │
         │                   │ scrapeado (0/1)  │
         │    matches        └────────┬─────────┘
         │    ┌────────────────┐      │
         └───→│ teletipo_id(FK)│      │
              │ articulo_id(FK)│◄─────┘
              │ score_titular  │
              │ score_cuerpo   │
              │ metodo         │
              │ fecha_deteccion│
              └────────────────┘
              UNIQUE(teletipo_id, articulo_id)
```

## Tabla: teletipos

Noticias generadas por la agencia. Importadas desde CSV/JSON.

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | TEXT PK | Identificador del teletipo (ej. "EP-2026-0501-001") |
| titular | TEXT NOT NULL | Titular del teletipo |
| cuerpo | TEXT | Texto completo o primer parrafo |
| fecha_emision | DATETIME NOT NULL | Cuando se emitio el teletipo |
| categoria | TEXT | Categoria tematica (politica, economia...) |

## Tabla: articulos

Articulos recogidos de medios via RSS.

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | INTEGER PK AUTO | ID interno |
| medio | TEXT NOT NULL | Identificador del medio (ej. "abc", "el_mundo") |
| seccion | TEXT | Seccion del feed (ej. "economia") |
| titular | TEXT NOT NULL | Titular del articulo |
| resumen | TEXT | Summary del RSS (HTML limpiado) |
| url | TEXT UNIQUE NOT NULL | Link al articulo |
| fecha_publicacion | DATETIME | Cuando se publico |
| fecha_ingesta | DATETIME DEFAULT NOW | Cuando lo recogimos |
| autor | TEXT | Autor/fuente extraido por Scrapling |
| cuerpo_completo | TEXT | Texto completo del articulo (Scrapling) |
| scrapeado | INTEGER DEFAULT 0 | 1 si ya fue scrapeado, 0 si no |

Los campos `autor`, `cuerpo_completo` y `scrapeado` se rellenan en el pase de scraping (Scrapling), no en la ingesta RSS.

## Tabla: matches

Relacion detectada entre un teletipo y un articulo.

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | INTEGER PK AUTO | ID interno |
| teletipo_id | TEXT FK → teletipos | El teletipo de la agencia |
| articulo_id | INTEGER FK → articulos | El articulo del medio |
| score_titular | REAL NOT NULL | Score fuzzy del titular (0-100) |
| score_cuerpo | REAL | Score fuzzy del cuerpo (0-100, opcional) |
| metodo | TEXT DEFAULT 'fuzzy' | Metodo: 'fuzzy', 'fuente', o 'scraping_fuzzy' |
| fecha_deteccion | DATETIME DEFAULT NOW | Cuando se detecto |

Constraint: UNIQUE(teletipo_id, articulo_id) — un mismo par no se duplica.

## Indices

| Indice | Tabla | Columna(s) | Motivo |
|--------|-------|------------|--------|
| idx_articulos_medio | articulos | medio | Filtrar por medio |
| idx_articulos_fecha | articulos | fecha_publicacion | Ventana temporal |
| idx_teletipos_fecha | teletipos | fecha_emision | Ventana temporal |
| idx_matches_teletipo | matches | teletipo_id | Buscar matches de un teletipo |
