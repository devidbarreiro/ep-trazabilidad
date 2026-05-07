# Alternativas evaluadas

Antes de llegar al enfoque actual (RSS + fuzzy matching), se evaluaron otras estrategias. Este documento explica por que se descartaron o se reservan para fases futuras.

## Herramientas comerciales (Meltwater, Factiva, etc.)

**Que hacen:** Plataformas SaaS de monitoring de medios. Indexan miles de fuentes, ofrecen alertas, analytics, dashboards.

**Por que no para el MVP:**
- Coste de miles de EUR/mes
- Sobredimensionado: no necesitamos indexar todo internet, solo N medios conocidos
- Lock-in con el proveedor
- La mayoria cobran por volumen de queries

**Cuando si tendria sentido:** Si la agencia necesitara monitoring de medios internacionales, redes sociales, TV/radio, o analisis de sentimiento. Para solo trackear "mis teletipos en mis clientes" es overkill.

## Google News scraping

**Que hace:** Usar busquedas tipo `site:abc.es "texto del teletipo"` para encontrar publicaciones.

**Por que no:**
- Ya sabemos donde buscar (nuestros clientes), no necesitamos que Google busque por nosotros
- Rate limiting de Google
- Legalmente gris
- Mas lento y fragil que RSS directo

**Cuando si tendria sentido:** Si quisieramos detectar publicaciones en medios que NO son clientes (republicaciones no autorizadas).

## GDELT Project

**Que hace:** Base de datos open source que monitoriza medios globales. Gratis, datos masivos.

**Por que no:**
- Demasiado generico para este caso
- Delay en la indexacion
- Filtrarlo a solo "nuestros clientes" es mas trabajo que ir directo al RSS

**Cuando si tendria sentido:** Para analisis macro de cobertura mediatica (no para tracking de teletipos concretos).

## Scraping directo (sin RSS)

**Que hace:** Scrapear las webs de los medios directamente con Scrapling, BeautifulSoup, etc.

**Por que no como primera opcion:**
- Los medios tienen RSS que ya da lo que necesitamos
- Scraping directo requiere mantener selectores CSS por medio
- Riesgo de bloqueo por rate limiting
- Mas codigo, mas mantenimiento

**Cuando si tendria sentido:** Como fallback para medios que no tengan RSS o cuyo RSS sea incompleto. Scrapling (que tenemos clonado) seria la herramienta para esto.

## Embeddings / LLMs

**Que hace:** Convertir titulares a vectores y buscar por similaridad coseno. O usar un LLM para comparar semanticamente.

**Por que no para el MVP:**
- Los medios suelen conservar los titulares casi igual → fuzzy matching funciona
- Coste de embeddings (aunque sea bajo, no es cero)
- Dependencia de modelos / APIs externas
- Complejidad innecesaria en esta fase

**Cuando si tendria sentido:** Si el fuzzy matching no alcanza >85% de precision con datos reales. Seria "fase 2": para los titulares que fueron muy reescritos, pasar a embeddings ligeros (sentence-transformers).

## Tabla resumen

| Enfoque | Coste | Cobertura | Complejidad | Fase |
|---------|-------|-----------|-------------|------|
| RSS + fuzzy match | 0 EUR | ~85-90% | Baja | **MVP (actual)** |
| + scraping fallback | ~0 EUR | ~93% | Media | Fase 1.5 |
| + embeddings | Bajo | ~98% | Alta | Fase 2 |
| Meltwater/Factiva | Miles EUR/mes | ~99% | Baja (SaaS) | Descartado |
