# El problema

## Contexto

Las agencias de noticias (Europa Press, EFE, etc.) generan decenas o cientos de teletipos al dia. Estos teletipos se venden a periodicos, radios, televisiones y medios digitales.

El flujo actual:

```
Agencia genera 100 teletipos/dia
        │
        ├──→ ABC compra 50
        ├──→ El Mundo compra 40
        ├──→ La Vanguardia compra 60
        └──→ ... N medios cliente
                    │
                    ▼
            Cada medio publica ALGUNOS
            (pueden ser 5, 10, 20...)
```

## El problema concreto

**La agencia no sabe cuales de sus teletipos fueron publicados por cada medio.**

- Los medios no informan que publicaron
- No hay un sistema de tracking estandar
- La agencia solo sabe que vendio, no que se uso

Esto significa que la agencia no puede:
- Medir el impacto real de sus teletipos
- Saber que tipo de contenido se publica mas
- Negociar tarifas basadas en uso real
- Dar feedback a sus redactores sobre alcance

## Por que es resoluble

Este problema tiene tres caracteristicas que lo hacen abordable:

### 1. Corpus conocido
La agencia ya tiene todos sus teletipos en una base de datos. No hay que "descubrir" contenido propio.

### 2. Destinos finitos
Los clientes son una lista cerrada: 20-50 medios conocidos. No hay que rastrear "todo internet".

### 3. Los medios respetan el contenido
Cuando un periodico publica un teletipo, normalmente:
- Mantiene el titular igual o con cambios menores
- Conserva el primer parrafo casi intacto
- Anade contexto propio pero la base es reconocible

Esto hace que la comparacion de strings sea suficiente para la mayoria de casos.

## Alternativas descartadas

| Alternativa | Por que no |
|-------------|------------|
| Pedir a los medios que informen | No quieren, no les interesa |
| Meltwater / Factiva | Miles de EUR/mes, overkill para esto |
| Google News scraping | Innecesario: ya sabemos donde buscar |
| GDELT | Datos masivos pero no necesarios aqui |
| Embeddings / LLMs | Sobreingenieria para el MVP, fuzzy matching basta |

## La solucion elegida

Monitorizar las webs de los medios cliente via RSS (gratis, legal, estructurado) y comparar los titulares contra los teletipos de la agencia usando fuzzy string matching.

Coste: 0 EUR. Complejidad: un script Python.
