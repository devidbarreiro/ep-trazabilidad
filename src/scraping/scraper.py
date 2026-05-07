import re
import time
from .fetch import fetch_page
from ..db import Database


AGENCIA_KEYWORDS = [
    "europa press",
    "europapress",
    "agencia efe",
    " efe,",
    " efe.",
    "(efe)",
]

BODY_SELECTORS = [
    "article p",
    "[class*='body'] p",
    "[class*='text'] p",
    "[class*='content'] p",
    "[itemprop='articleBody'] p",
    ".article-body p",
]

AUTHOR_SELECTORS = [
    'meta[name="author"]',
    'meta[property="article:author"]',
    '[class*="author"]',
    '[class*="firma"]',
    '[class*="byline"]',
    '[itemprop="author"]',
    '[rel="author"]',
]


class ArticleScraper:
    def __init__(self, db: Database, agencia: str = "europa press", delay: float = 1.0):
        self.db = db
        self.agencia = agencia.lower()
        self.agencia_keywords = AGENCIA_KEYWORDS + [agencia.lower()]
        self.delay = delay

    def scrape_articulo(self, url: str) -> dict | None:
        try:
            page = fetch_page(url)
        except Exception:
            return None

        autor = self._extract_autor(page)
        cuerpo = self._extract_cuerpo(page)
        fuente_detectada = self._detectar_fuente(page, autor)

        return {
            "autor": autor,
            "cuerpo": cuerpo,
            "fuente_detectada": fuente_detectada,
        }

    def scrape_pendientes(self, limit: int = 50) -> dict:
        articulos = self.db.get_articulos_sin_match_no_scrapeados()
        if limit:
            articulos = articulos[:limit]

        stats = {"total": len(articulos), "scrapeados": 0, "errores": 0, "fuente_directa": 0}

        for art in articulos:
            result = self.scrape_articulo(art["url"])

            if result is None:
                stats["errores"] += 1
                self.db.update_articulo_scraping(art["id"], autor=None, cuerpo_completo=None)
                continue

            self.db.update_articulo_scraping(
                art["id"],
                autor=result["autor"],
                cuerpo_completo=result["cuerpo"],
            )
            stats["scrapeados"] += 1

            if result["fuente_detectada"]:
                stats["fuente_directa"] += 1

            if self.delay > 0:
                time.sleep(self.delay)

        return stats

    def _extract_autor(self, page) -> str | None:
        for selector in AUTHOR_SELECTORS:
            elements = page.css(selector)
            if not elements:
                continue

            if selector.startswith("meta"):
                content = elements[0].attrib.get("content", "").strip()
                if content:
                    return content
            else:
                texts = elements.css("::text").getall()
                text = " ".join(t.strip() for t in texts if t.strip())
                if text:
                    return text

        return None

    def _extract_cuerpo(self, page) -> str | None:
        for selector in BODY_SELECTORS:
            paragraphs = page.css(selector)
            if not paragraphs:
                continue

            texts = []
            for p in paragraphs:
                text = " ".join(t.strip() for t in p.css("::text").getall() if t.strip())
                if len(text) > 30:
                    texts.append(text)

            if texts:
                return "\n\n".join(texts)

        return None

    def _detectar_fuente(self, page, autor: str | None) -> bool:
        if autor:
            autor_lower = autor.lower()
            for keyword in self.agencia_keywords:
                if keyword in autor_lower:
                    return True

        all_text = page.get_all_text().lower()
        for keyword in self.agencia_keywords:
            if keyword in all_text:
                return True

        return False
