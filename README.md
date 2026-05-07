# EP Trazabilidad

Sistema de trazabilidad de teletipos para agencias de noticias. Detecta automaticamente que noticias propias han sido publicadas por medios cliente, sin depender de que estos informen.

## El problema

Una agencia de noticias genera ~100 teletipos al dia y los vende a periodicos (ABC, El Mundo, El Pais...). Cada periodico compra un subconjunto y publica solo algunos. **La agencia no tiene forma de saber cuales de sus noticias fueron publicadas ni por quien.**

Este sistema resuelve eso: monitoriza los medios cliente, compara contra los teletipos de la agencia, y genera un registro de trazabilidad.

## Como funciona

El sistema usa dos pases de deteccion complementarios:

```
Teletipos de la agencia              Articulos de medios
        │                                     │
        │                          ┌──────────┴──────────┐
        │                          │                     │
        │                    feedparser              Scrapling
        │                   (lee RSS: titulares,    (abre la URL:
        │                    resumen, fecha)         texto completo,
        │                          │                 autor, fuente)
        │                          │                     │
        └────────┬─────────────────┴─────────────────────┘
                 │
        ┌────────┴────────┐
        │   PASE 1        │  Fuzzy match por titular (RapidFuzz)
        │   ~85-90% hits  │  Rapido, cubre la mayoria de casos
        └────────┬────────┘
                 │
        ┌────────┴────────┐
        │   PASE 2        │  Solo para los que NO matchearon:
        │   +5-10% hits   │  - Detecta fuente ("Europa Press" en autor/texto)
        │                 │  - Fuzzy match por cuerpo completo
        └────────┬────────┘
                 │
                 ▼
        Registro de trazabilidad
   "Tu teletipo X fue publicado por ABC el dia Y"
```

**No usa IA/LLMs, no necesita API keys.** Solo Python + comparacion de strings + scraping.

## Quick start

```bash
# 1. Instalar
cd ep-trazabilidad
python3 -m venv .venv && source .venv/bin/activate
pip install feedparser rapidfuzz rich pyyaml scrapling curl_cffi playwright

# 2. Cargar teletipos (CSV o JSON con: id, titular, cuerpo, fecha_emision)
python -m src.cli load data/teletipos_ejemplo.csv

# 3. Ciclo rapido (solo RSS + matching titular)
python -m src.cli run

# 4. Ciclo completo (RSS + matching + scraping + deep matching)
python -m src.cli run-full

# 5. Ver resultados
python -m src.cli report
python -m src.cli report --format csv > resultados.csv
```

## Comandos

| Comando | Que hace |
|---------|----------|
| `load <archivo>` | Cargar teletipos desde CSV o JSON |
| `ingest` | Recoger articulos de medios via RSS (feedparser) |
| `match` | Pase 1: fuzzy matching por titular (RapidFuzz) |
| `scrape` | Scrapear articulos sin match con Scrapling (texto completo + autor) |
| `deep-match` | Pase 2: matching por cuerpo completo + deteccion de fuente |
| `run` | Ciclo rapido: ingest + match |
| `run-full` | Ciclo completo: ingest + match + scrape + deep-match |
| `report` | Ver matches (--format table/json/csv) |
| `stats` | Estado de la base de datos |

## Medios preconfigurados

7 medios con 19 feeds RSS verificados:

| Medio | Secciones |
|-------|-----------|
| ABC | portada, espana, economia |
| El Mundo | portada, espana, economia |
| El Pais | portada, espana, economia |
| La Vanguardia | portada, politica, economia |
| 20 Minutos | portada, nacional |
| El Confidencial | espana, economia |
| elDiario.es | portada, politica, economia |

Anadir un medio nuevo: editar `config/feeds.yaml`.

## Stack

| Componente | Libreria | Funcion |
|------------|----------|---------|
| Ingesta RSS | feedparser | Descubrir articulos nuevos (titulares, fechas, URLs) |
| Scraping | Scrapling | Extraer texto completo + autor de articulos |
| Matching | RapidFuzz | Comparacion fuzzy de titulares y cuerpos |
| Base de datos | SQLite | Almacenamiento local, zero-config |
| CLI | argparse + Rich | Interfaz de comandos con tablas |
| Config | PyYAML | Configuracion de feeds y umbrales |

## Como encajan feedparser y Scrapling

No es uno u otro — son complementarios:

| | feedparser (RSS) | Scrapling (scraping) |
|---|---|---|
| **Que hace** | Lee el indice de noticias | Abre la pagina real del articulo |
| **Que da** | Titular, resumen, fecha, URL | Texto completo, autor, fuente |
| **Velocidad** | ~1000 articulos/segundo | ~1 articulo/segundo |
| **Cuando se usa** | Siempre (pase 1) | Solo articulos sin match (pase 2) |

feedparser descubre QUE se publico. Scrapling extrae el CONTENIDO completo.

## Documentacion

- [`docs/problema/`](docs/problema/) — Contexto del negocio y por que este enfoque
- [`docs/arquitectura/`](docs/arquitectura/) — Modulos, esquema de datos, flujo de 2 pases
- [`docs/uso/`](docs/uso/) — Guia de uso, configuracion, formatos de datos
- [`docs/desarrollo/`](docs/desarrollo/) — Decisiones tecnicas, roadmap, futuras mejoras

## Estado actual

**MVP funcional con 2 pases.** Ingesta probada con 1117 articulos reales de 7 medios. Scraping verificado con Scrapling (extrae autor y cuerpo completo). Matching en 2 pases: titular (fuzzy) + cuerpo/fuente (deep). Falta cargar teletipos reales para medir precision en produccion.
