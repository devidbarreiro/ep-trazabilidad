# Formatos de datos

## Teletipos — CSV

El archivo CSV debe tener cabecera con estos campos:

| Campo | Obligatorio | Descripcion |
|-------|:-----------:|-------------|
| id | Si | Identificador unico del teletipo |
| titular | Si | Titular de la noticia |
| cuerpo | No | Texto completo o primer parrafo |
| fecha_emision | Si | Fecha/hora en formato ISO 8601 |
| categoria | No | Categoria tematica |

**Ejemplo:**

```csv
id,titular,cuerpo,fecha_emision,categoria
EP-2026-0501-001,"El Gobierno aprueba el plan de vivienda para jovenes","El Consejo de Ministros ha dado luz verde al nuevo plan...",2026-05-01T10:30:00,politica
EP-2026-0501-002,"Espana registra un crecimiento del PIB del 2,4%","La economia espanola crecio un 2,4% interanual...",2026-05-01T09:00:00,economia
```

**Notas:**
- Encoding: UTF-8
- Separador: coma
- Campos con comas deben ir entre comillas dobles
- El campo `cuerpo` mejora la precision del matching pero no es estrictamente necesario

## Teletipos — JSON

Array de objetos con los mismos campos:

```json
[
  {
    "id": "EP-2026-0501-001",
    "titular": "El Gobierno aprueba el plan de vivienda para jovenes",
    "cuerpo": "El Consejo de Ministros ha dado luz verde al nuevo plan...",
    "fecha_emision": "2026-05-01T10:30:00",
    "categoria": "politica"
  },
  {
    "id": "EP-2026-0501-002",
    "titular": "Espana registra un crecimiento del PIB del 2,4%",
    "cuerpo": "La economia espanola crecio un 2,4% interanual...",
    "fecha_emision": "2026-05-01T09:00:00",
    "categoria": "economia"
  }
]
```

## Output de report — CSV

Cuando se ejecuta `python -m src.cli report --format csv`, el output tiene estos campos:

```csv
teletipo_id,teletipo_titular,medio,articulo_titular,score_titular,fecha_publicacion,url
EP-2026-0501-001,"El Gobierno aprueba el plan de vivienda...",abc,"El Gobierno aprueba el plan de vivienda para jovenes menores de 35",95,2026-05-01T14:30:00,https://www.abc.es/...
```

## Output de report — JSON

```json
[
  {
    "teletipo_id": "EP-2026-0501-001",
    "teletipo_titular": "El Gobierno aprueba el plan de vivienda...",
    "medio": "abc",
    "articulo_titular": "El Gobierno aprueba el plan de vivienda para jovenes menores de 35",
    "score_titular": 95.0,
    "score_cuerpo": 72.0,
    "fecha_publicacion": "2026-05-01T14:30:00",
    "url": "https://www.abc.es/..."
  }
]
```
