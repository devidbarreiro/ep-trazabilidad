# Decisiones tecnicas

Registro de decisiones clave y su justificacion.

## 1. RSS sobre scraping directo

**Decision:** Usar feeds RSS como fuente principal de articulos de medios.

**Contexto:** Los medios podrian scrapearse directamente (HTML) o via RSS.

**Motivo:**
- Gratis y legal sin ambiguedad
- Ya viene estructurado (titulo, fecha, resumen parseados)
- No requiere mantener selectores CSS por medio
- No hay riesgo de bloqueo por rate limiting
- feedparser es una libreria madura y estable

**Limitacion aceptada:** Algunos medios pueden tener RSS incompleto, retrasado, o sin resumen. Se evalua caso por caso, y Scrapling queda como fallback para scraping directo si fuera necesario.

## 2. feedparser sobre Scrapling para RSS

**Decision:** Usar `feedparser` en lugar de Scrapling para parsear RSS.

**Contexto:** Scrapling es un framework de web scraping. feedparser es una libreria especifica para RSS/Atom.

**Motivo:**
- feedparser es la libreria estandar de facto para RSS en Python
- Maneja todas las variantes de RSS (0.9x, 1.0, 2.0) y Atom
- Parsea fechas, autores, categorias automaticamente
- Es mas ligero que Scrapling para este caso de uso
- Scrapling brilla en scraping de HTML, no en parsear XML/RSS

**Relacion con Scrapling:** feedparser y Scrapling son complementarios, no excluyentes. feedparser lee el indice (RSS) — rapido, gratis, ligero. Scrapling abre la URL real del articulo y extrae el contenido completo de la pagina HTML (titulo, subtitulo, cuerpo completo, autor, tags). Ver decision #7 para el flujo integrado.

## 3. RapidFuzz sobre embeddings

**Decision:** Fuzzy string matching (RapidFuzz) como motor de comparacion, no embeddings.

**Contexto:** Hay dos familias de enfoque:
- String matching: compara caracteres/tokens directamente
- Semantic matching: convierte a vectores y compara por distancia

**Motivo:**
- Los medios suelen conservar titulares casi intactos (cambian articulos, anaden coletillas)
- `partial_ratio` detecta subcadenas: "Gobierno aprueba plan" dentro de "El Gobierno aprueba el plan de vivienda para jovenes" → score alto
- RapidFuzz esta implementado en C, es extremadamente rapido
- Zero-cost: no necesita modelos, APIs, GPU
- Resultado determinista y explicable (es un numero, no una "probabilidad")

**Limitacion aceptada:** Si un medio reescribe completamente el titular, fuzzy matching no lo detecta. Esto se reserva para una posible fase 2 con embeddings.

## 4. SQLite sobre PostgreSQL

**Decision:** SQLite como base de datos.

**Motivo:**
- Zero configuracion, un solo archivo
- Suficiente para el volumen: ~100 teletipos/dia × ~1000 articulos/dia
- Facil de backup (copiar un archivo)
- WAL mode activado para mejor rendimiento en escrituras concurrentes
- Migracion a PostgreSQL es trivial si se escala

## 5. Ventana temporal de ±48h

**Decision:** Solo comparar articulos publicados dentro de ±48h del teletipo.

**Motivo:**
- Los medios publican teletipos el mismo dia o al siguiente
- Reduce el espacio de busqueda en ~95% (de miles a decenas de candidatos)
- Evita falsos positivos con noticias tematicamente similares de semanas distintas

## 7. Flujo integrado feedparser + Scrapling (dos pases)

**Decision:** Usar un sistema de dos pases — feedparser para descubrir articulos, Scrapling solo como refuerzo para los que no matchean por titular.

**Contexto:** feedparser (RSS) da titular + resumen pero NO el texto completo del articulo. Scrapling puede abrir la URL y extraer todo el contenido HTML, incluyendo cuerpo completo y campo autor/fuente. La diferencia clave:

| Dato                              | feedparser (RSS) | Scrapling (scraping) |
|-----------------------------------|:----------------:|:--------------------:|
| Titular del articulo              | Si               | Si                   |
| Resumen (~150 chars)              | Si               | Si                   |
| Texto completo del articulo       | No               | Si                   |
| Autor / fuente (ej. "Europa Press") | No             | Si (a veces)         |
| Fotos, multimedia                 | No               | Si                   |

**Flujo propuesto:**

```
1. feedparser lee RSS → lista de articulos nuevos (titular + URL)
2. Fuzzy match por titular → si score >= 80 → match confirmado, listo
3. Para los que NO matchean por titular:
   → Scrapling abre la URL del articulo
   → Extrae texto completo + campo autor
   → Si autor contiene "Europa Press" → match directo (sin fuzzy)
   → Si no, fuzzy match con texto completo → mas chances de detectar
```

**Por que este orden:**
- No scrapeamos las 1000+ URLs de cada ciclo (caro, lento)
- Solo scrapeamos las que el primer pase no resuelve (~10-15% estimado)
- Lo mejor de los dos mundos: velocidad de RSS + profundidad de scraping

**Impacto esperado en cobertura:**
- Solo RSS + fuzzy titular: ~85-90%
- Con Scrapling en segundo pase: ~95%+ (texto completo mejora matching + deteccion directa por campo autor)

**Estado:** Pendiente de implementar. El MVP actual solo usa el pase 1 (feedparser + fuzzy).

## 6. Score de cuerpo informativo, no bloqueante

**Decision:** El score del cuerpo/resumen se calcula y se guarda, pero NO bloquea un match si el titular coincide.

**Contexto:** Inicialmente, si el score del cuerpo era bajo, se descartaba el match aunque el titular coincidiera. Esto causaba falsos negativos porque los resumenes de RSS suelen ser muy diferentes del cuerpo del teletipo original.

**Motivo:**
- El titular es el indicador mas fiable de coincidencia
- Los resumenes RSS son a menudo extractos parciales o reescritos
- El score del cuerpo sigue disponible para filtrar en reportes si se quiere mas precision
