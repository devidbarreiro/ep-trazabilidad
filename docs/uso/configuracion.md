# Configuracion

Toda la configuracion esta en `config/`. Dos archivos YAML.

## config/feeds.yaml — Medios y feeds RSS

Define los medios a monitorizar y sus feeds RSS.

```yaml
medios:
  abc:                                          # ID interno del medio
    nombre: "ABC"                               # Nombre para mostrar
    feeds:
      - url: "https://www.abc.es/rss/2.0/portada/"
        seccion: "portada"
      - url: "https://www.abc.es/rss/2.0/espana/"
        seccion: "espana"
```

### Medios preconfigurados

| ID | Nombre | Feeds |
|----|--------|-------|
| `abc` | ABC | portada, espana, economia |
| `el_mundo` | El Mundo | portada, espana, economia |
| `el_pais` | El Pais | portada, espana, economia |
| `la_vanguardia` | La Vanguardia | portada, politica, economia |
| `20_minutos` | 20 Minutos | portada, nacional |
| `el_confidencial` | El Confidencial | espana, economia |
| `eldiario` | elDiario.es | portada, politica, economia |

### Anadir un medio nuevo

1. Buscar los feeds RSS del medio (normalmente en `/rss/` o `/feed/`)
2. Verificar que devuelven XML: `curl -s "URL" | head -5`
3. Anadir al YAML:

```yaml
  nuevo_medio:
    nombre: "Nombre del Medio"
    feeds:
      - url: "https://ejemplo.com/rss/portada.xml"
        seccion: "portada"
```

### Como encontrar feeds RSS de un medio

- Probar: `/rss/`, `/feed/`, `/feeds/`, `/rss/index.xml`
- Buscar en el HTML: `<link rel="alternate" type="application/rss+xml">`
- Google: `site:ejemplo.com rss OR feed`

## config/settings.yaml — Parametros del sistema

```yaml
matching:
  umbral_titular: 80    # Score minimo (0-100) para match por titular (pase 1)
  umbral_cuerpo: 70     # Score minimo para match por cuerpo (pase 2)
  ventana_horas: 48     # Buscar teletipos emitidos ±N horas del articulo

ingesta:
  intervalo_minutos: 30
  user_agent: "EPTrazabilidad/0.1 (feed reader)"

scraping:
  agencia: "europa press"            # Nombre de la agencia
  agencia_keywords:                  # Keywords para detectar fuente en articulos
    - "europa press"
    - "europapress"
    - "ep/"
  delay: 1.0                         # Segundos entre requests (evitar bloqueos)

db:
  path: "data/trazabilidad.db"
```

### Ajustar umbrales de matching

| Umbral | Efecto al subir | Efecto al bajar |
|--------|-----------------|-----------------|
| `umbral_titular` | Menos falsos positivos, puede perder matches reales | Mas matches, mas ruido |
| `ventana_horas` | Busca en mas rango, mas lento | Mas rapido, puede perder publicaciones tardias |

**Recomendacion:** empezar con los defaults (80 / 48h), revisar los matches con `report`, y ajustar si:
- Hay demasiados falsos positivos → subir `umbral_titular` a 85-90
- Se pierden matches obvios → bajar a 70-75

### Configurar scraping (Scrapling)

| Parametro | Default | Descripcion |
|-----------|---------|-------------|
| `agencia` | "europa press" | Nombre de tu agencia |
| `agencia_keywords` | ["europa press", "europapress", "ep/"] | Variantes para detectar en autor/texto |
| `delay` | 1.0 | Pausa entre requests en segundos |

**Sobre el delay:** 1 segundo es conservador. Si scrapeas pocos articulos (<50) puedes bajar a 0.5. Si scrapeas muchos (>200), sube a 2.0 para evitar rate limiting.

**Sobre las keywords:** los medios citan la fuente de formas variadas ("Europa Press", "EP", "EuropaPress"). Anade todas las variantes que veas en los articulos reales.
