# Desarrollo

## Estado actual

**MVP funcional.** El sistema:
- Ingesta RSS de 7 medios (19 feeds, todos verificados y funcionando)
- Almacena en SQLite
- Hace fuzzy matching por titular
- Genera reportes en tabla/CSV/JSON
- Probado con 1073 articulos reales

**Falta:** validar con teletipos reales de la agencia para medir precision real.

## Estructura del codigo

```
ep-trazabilidad/
├── README.md                  ← Overview y quick start
├── pyproject.toml             ← Dependencias y metadata
│
├── config/
│   ├── feeds.yaml             ← Medios y sus feeds RSS
│   └── settings.yaml          ← Umbrales, ventana temporal, DB path
│
├── data/
│   ├── teletipos_ejemplo.csv  ← Datos de prueba
│   └── trazabilidad.db        ← Base de datos SQLite (generada)
│
├── src/
│   ├── __init__.py
│   ├── cli.py                 ← CLI con 6 comandos (argparse + Rich)
│   ├── config.py              ← Carga de YAML configs
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py        ← Clase Database: tablas, queries, indices
│   ├── ingesta/
│   │   ├── __init__.py
│   │   └── rss.py             ← RSSIngester: feedparser → SQLite
│   └── matching/
│       ├── __init__.py
│       └── matcher.py         ← Matcher: RapidFuzz fuzzy matching
│
└── docs/
    ├── problema/              ← Contexto de negocio
    ├── arquitectura/          ← Diseno tecnico
    ├── uso/                   ← Guia de uso
    └── desarrollo/            ← Decisiones, roadmap, contribuir
```

## Dependencias

| Libreria | Version | Para que |
|----------|---------|----------|
| feedparser | >=6.0 | Parsear RSS/Atom feeds |
| rapidfuzz | >=3.0 | Fuzzy string matching (C, muy rapido) |
| rich | >=13.0 | Tablas bonitas en terminal |
| pyyaml | >=6.0 | Leer configs YAML |

Zero dependencias pesadas. No requiere numpy, torch, ni nada de ML.

## Documentos relacionados

- [Decisiones tecnicas](decisiones.md) — Por que cada eleccion
- [Roadmap](roadmap.md) — Siguientes pasos y futuras mejoras
