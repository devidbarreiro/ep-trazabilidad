# Guia de uso

## Instalacion

```bash
cd ep-trazabilidad
python3 -m venv .venv
source .venv/bin/activate
pip install feedparser rapidfuzz rich pyyaml scrapling curl_cffi playwright
```

Requisitos: Python 3.10+ (recomendado 3.13). No necesita Docker, bases de datos externas, ni API keys.

## Comandos disponibles

Todos los comandos se ejecutan con `python -m src.cli <comando>`.

### `load` — Cargar teletipos

Importa los teletipos de la agencia desde un archivo local.

```bash
python -m src.cli load data/teletipos.csv
python -m src.cli load data/teletipos.json
```

Ver [formatos de datos](formatos.md) para la estructura esperada.

### `ingest` — Recoger articulos (feedparser + RSS)

Parsea los feeds RSS de todos los medios configurados y guarda los articulos nuevos.

```bash
python -m src.cli ingest                      # todos los medios
python -m src.cli ingest --medio abc el_mundo  # solo algunos
```

### `match` — Pase 1: matching por titular (RapidFuzz)

Compara titulares de articulos vs teletipos con fuzzy matching.

```bash
python -m src.cli match
```

### `scrape` — Scrapear articulos sin match (Scrapling)

Abre las URLs de articulos que no matchearon y extrae texto completo + autor.

```bash
python -m src.cli scrape              # hasta 50 articulos (default)
python -m src.cli scrape --limit 100  # hasta 100
```

### `deep-match` — Pase 2: matching por cuerpo + fuente

Usa los datos de scraping para detectar matches adicionales.

```bash
python -m src.cli deep-match
```

### `run` — Ciclo rapido (solo RSS)

Ejecuta ingest + match. Rapido, sin scraping.

```bash
python -m src.cli run
```

### `run-full` — Ciclo completo (RSS + scraping)

Los 4 pasos: ingest + match + scrape + deep-match.

```bash
python -m src.cli run-full              # scrape hasta 50 articulos
python -m src.cli run-full --limit 100  # scrape hasta 100
```

### `report` — Ver resultados

```bash
python -m src.cli report                    # tabla en terminal
python -m src.cli report --format csv       # exportar CSV
python -m src.cli report --format json      # JSON
python -m src.cli report --min-score 90     # solo matches fuertes
```

### `stats` — Estado de la base de datos

```bash
python -m src.cli stats
```

```
┌──────────────────────┬───────┐
│ Metrica              │ Valor │
├──────────────────────┼───────┤
│ Teletipos cargados   │    10 │
│ Articulos ingestados │  1117 │
│ Articulos scrapeados │     8 │
│ Matches detectados   │    15 │
│ Medios con articulos │     7 │
└──────────────────────┴───────┘
```

## Uso tipico diario

### Opcion rapida (~1 minuto)
```bash
python -m src.cli load teletipos_hoy.csv   # si hay nuevos
python -m src.cli run                       # RSS + matching titular
python -m src.cli report
```

### Opcion completa (~5-10 minutos)
```bash
python -m src.cli load teletipos_hoy.csv
python -m src.cli run-full --limit 100      # RSS + matching + scraping + deep
python -m src.cli report --format csv > resultados.csv
```

### Automatizar con cron

```bash
# Cada hora, ciclo rapido
0 * * * * cd /path/to/ep-trazabilidad && .venv/bin/python -m src.cli run

# Cada 6 horas, ciclo completo
0 */6 * * * cd /path/to/ep-trazabilidad && .venv/bin/python -m src.cli run-full --limit 200
```

## Documentos relacionados

- [Formatos de datos](formatos.md) — Estructura de CSV y JSON para teletipos
- [Configuracion](configuracion.md) — Feeds RSS, umbrales de matching, scraping settings
