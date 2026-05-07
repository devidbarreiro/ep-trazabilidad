import feedparser
from datetime import datetime
from time import mktime
from ..db import Database


class RSSIngester:
    def __init__(self, db: Database, user_agent: str = "EPTrazabilidad/0.1"):
        self.db = db
        self.user_agent = user_agent

    def ingest_feed(self, medio_id: str, feed_url: str, seccion: str | None = None) -> int:
        feed = feedparser.parse(feed_url, agent=self.user_agent)
        nuevos = 0

        for entry in feed.entries:
            titular = entry.get("title", "").strip()
            if not titular:
                continue

            url = entry.get("link", "")
            if not url:
                continue

            resumen = entry.get("summary", entry.get("description", ""))
            if resumen:
                resumen = _strip_html(resumen).strip()

            fecha = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                fecha = datetime(*entry.published_parsed[:6]).isoformat()
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                fecha = datetime(*entry.updated_parsed[:6]).isoformat()

            row_id = self.db.insert_articulo(
                medio=medio_id,
                seccion=seccion,
                titular=titular,
                resumen=resumen,
                url=url,
                fecha_publicacion=fecha,
            )
            if row_id is not None:
                nuevos += 1

        return nuevos

    def ingest_medio(self, medio_id: str, feeds: list[dict]) -> int:
        total = 0
        for feed_conf in feeds:
            total += self.ingest_feed(medio_id, feed_conf["url"], feed_conf.get("seccion"))
        return total


def _strip_html(text: str) -> str:
    import re
    clean = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", clean)
