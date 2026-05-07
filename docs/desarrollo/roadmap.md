# Roadmap

## Fase actual: MVP (completada)

- [x] Ingesta RSS de 7 medios (19 feeds verificados)
- [x] Almacenamiento SQLite con esquema relacional
- [x] Motor de fuzzy matching por titular
- [x] CLI con 6 comandos (load, ingest, match, run, report, stats)
- [x] Export a tabla/CSV/JSON
- [x] Datos de prueba
- [x] Documentacion

## Siguiente: Validacion con datos reales

**Objetivo:** Cargar teletipos reales y medir precision.

- [ ] Obtener CSV de teletipos reales de un dia
- [ ] Ejecutar `run` y revisar matches
- [ ] Medir: % de matches correctos (precision) y % de matches encontrados (recall)
- [ ] Ajustar umbral_titular si es necesario
- [ ] Documentar resultados

## Fase 1.5: Scraping fallback (si RSS no basta)

**Objetivo:** Cubrir medios sin RSS adecuado o con RSS incompleto.

- [ ] Identificar medios donde el RSS no tiene suficiente informacion
- [ ] Usar Scrapling para scraping directo de esos medios
- [ ] Extraer texto completo del articulo para mejor matching
- [ ] Integrar como fuente adicional junto a RSS

## Fase 2: Embeddings (si fuzzy no basta)

**Objetivo:** Detectar matches donde el titular fue reescrito significativamente.

- [ ] Evaluar sentence-transformers (modelos pequenos, local)
- [ ] Generar embeddings de titulares al cargar teletipos
- [ ] Busqueda por similaridad coseno como segundo pase
- [ ] Solo para articulos que no matchearon con fuzzy

## Fase 3: Automatizacion y monitoring

**Objetivo:** Que funcione solo, sin intervencion manual.

- [ ] Cron job cada 30 minutos
- [ ] Notificaciones (email/Slack) cuando se detectan matches nuevos
- [ ] Dashboard web simple (FastAPI + htmx?)
- [ ] Alertas si un medio deja de publicar teletipos (cambio de contrato?)

## Fase 4: Analytics

**Objetivo:** Extraer insights del historico de matches.

- [ ] Que tipo de teletipos se publican mas (por categoria)
- [ ] Que medios publican mas teletipos (ranking)
- [ ] Tiempo medio entre emision y publicacion
- [ ] Tendencias a lo largo del tiempo
- [ ] Exportar datos para BI (Metabase, Grafana, etc.)

## Ideas para el futuro (sin priorizar)

- Detectar republicaciones no autorizadas (medios que no son clientes)
- Comparar como reescriben los medios los teletipos
- Detectar si anaden sesgo o contexto propio
- API REST para integrar con otros sistemas de la agencia
- Multi-idioma (teletipos en catalan, euskera, gallego)
