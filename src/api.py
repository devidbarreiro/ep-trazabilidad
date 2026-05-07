import threading
from datetime import datetime
from fastapi import FastAPI, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import load_feeds, load_settings, PROJECT_ROOT
from .db import Database
from .ingesta import RSSIngester
from .matching import Matcher

app = FastAPI(title="EP Trazabilidad API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = load_settings()
feeds_config = load_feeds()


def get_db() -> Database:
    return Database(str(PROJECT_ROOT / settings["db"]["path"]))


@app.get("/api/stats")
def stats():
    db = get_db()
    result = db.get_stats()
    db.close()
    return result


@app.get("/api/matches")
def matches(
    min_score: float = Query(0),
    medio: str | None = Query(None),
    metodo: str | None = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
):
    db = get_db()
    all_matches = db.get_matches(min_score=min_score)
    db.close()

    results = [dict(m) for m in all_matches]
    if medio:
        results = [m for m in results if m["medio"] == medio]
    if metodo:
        results = [m for m in results if m["metodo"] == metodo]

    total = len(results)
    results = results[offset : offset + limit]
    return {"total": total, "matches": results}


@app.get("/api/medios")
def medios():
    return {
        mid: {"nombre": conf["nombre"], "feeds": len(conf["feeds"])}
        for mid, conf in feeds_config["medios"].items()
    }


@app.get("/api/articulos/recientes")
def articulos_recientes(limit: int = Query(20)):
    db = get_db()
    rows = db.conn.execute(
        "SELECT id, medio, titular, url, fecha_publicacion, scrapeado FROM articulos ORDER BY fecha_ingesta DESC LIMIT ?",
        (limit,),
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


class TeletipoIn(BaseModel):
    id: str
    titular: str
    cuerpo: str = ""
    fecha_emision: str
    categoria: str = ""


@app.post("/api/teletipos")
def add_teletipos(teletipos: list[TeletipoIn]):
    db = get_db()
    count = 0
    for t in teletipos:
        db.insert_teletipo(t.id, t.titular, t.cuerpo, t.fecha_emision, t.categoria)
        count += 1
    db.close()
    return {"loaded": count}


@app.post("/api/teletipos/upload")
async def upload_teletipos(file: UploadFile = File(...)):
    import csv
    import io
    import json

    content = await file.read()
    text = content.decode("utf-8")
    db = get_db()
    count = 0

    if file.filename and file.filename.endswith(".json"):
        data = json.loads(text)
        for t in data:
            db.insert_teletipo(t["id"], t["titular"], t.get("cuerpo", ""), t["fecha_emision"], t.get("categoria", ""))
            count += 1
    else:
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            db.insert_teletipo(row["id"], row["titular"], row.get("cuerpo", ""), row["fecha_emision"], row.get("categoria", ""))
            count += 1

    db.close()
    return {"loaded": count, "filename": file.filename}


@app.post("/api/teletipos/import-ep")
def import_europa_press():
    import feedparser

    feeds = [
        "https://www.europapress.es/rss/rss.aspx",
        "https://www.europapress.es/rss/rss.aspx?ch=00066",
        "https://www.europapress.es/rss/rss.aspx?ch=00069",
    ]

    db = get_db()
    seen = set()
    count = 0

    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.get("title", "").strip()
            if not title or title in seen:
                continue
            seen.add(title)

            desc = entry.get("description", "").strip()
            fecha = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                fecha = datetime(*entry.published_parsed[:6]).isoformat()
            cat = entry.get("category", "general")
            link = entry.get("link", "")
            ep_id = f"EP-{link.split('-')[-1].split('.')[0]}" if link else f"EP-AUTO-{count}"

            db.insert_teletipo(ep_id, title, desc, fecha or datetime.now().isoformat(), cat)
            count += 1

    db.close()
    return {"loaded": count}


class ScrapeURL(BaseModel):
    url: str


@app.post("/api/teletipos/from-url")
def teletipo_from_url(body: ScrapeURL):
    from scrapling.fetchers import Fetcher
    import hashlib

    page = Fetcher.get(body.url)

    titular = (page.css("h1::text").get() or "").strip()
    if not titular:
        return {"error": "No se pudo extraer el titular"}

    cuerpo = ""
    for meta in page.css('meta[name="description"], meta[property="og:description"]'):
        cuerpo = (meta.attrib.get("content") or "").strip()
        if cuerpo:
            break

    if not cuerpo:
        for p in page.css("article p, .article-body p, p"):
            text = " ".join(t.strip() for t in p.css("::text").getall() if t.strip())
            if len(text) > 40:
                cuerpo = text
                break

    fecha = ""
    for meta in page.css('meta[property="article:published_time"], meta[name="date"]'):
        fecha = (meta.attrib.get("content") or "").strip()
        if fecha:
            break
    if not fecha:
        fecha = datetime.now().isoformat()

    categoria = ""
    for sel in ['meta[name="section"]', 'meta[property="article:section"]', 'meta[property="article:tag"]']:
        for meta in page.css(sel):
            categoria = (meta.attrib.get("content") or "").strip()
            if categoria:
                break
        if categoria:
            break
    if not categoria:
        try:
            categoria = body.url.split("europapress.es/")[1].split("/")[0].capitalize()
        except (IndexError, AttributeError):
            pass

    url_hash = hashlib.md5(body.url.encode()).hexdigest()[:8]
    ep_id = f"EP-{url_hash}"

    db = get_db()
    db.insert_teletipo(ep_id, titular, cuerpo, fecha, categoria)
    db.close()

    return {
        "id": ep_id,
        "titular": titular,
        "cuerpo": cuerpo[:200],
        "fecha_emision": fecha,
        "categoria": categoria,
    }


@app.post("/api/reset")
def reset_db():
    db = get_db()
    db.conn.execute("DELETE FROM matches")
    db.conn.execute("DELETE FROM articulos")
    db.conn.commit()
    stats = db.get_stats()
    db.close()
    return {"status": "ok", "teletipos_conservados": stats["teletipos"]}


@app.get("/api/teletipos")
def list_teletipos(limit: int = Query(50)):
    db = get_db()
    rows = db.conn.execute(
        "SELECT * FROM teletipos ORDER BY fecha_emision DESC LIMIT ?", (limit,)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


_run_lock = threading.Lock()
_run_status = {"running": False, "last_result": None}


@app.get("/api/run/status")
def run_status():
    return _run_status


@app.post("/api/run")
def run_cycle():
    if _run_status["running"]:
        return {"status": "already_running"}

    def _run():
        _run_status["running"] = True
        _run_status["last_result"] = None
        try:
            db = get_db()
            ingester = RSSIngester(db, user_agent=settings["ingesta"]["user_agent"])
            total_ingested = 0
            for medio_id, conf in feeds_config["medios"].items():
                total_ingested += ingester.ingest_medio(medio_id, conf["feeds"])

            matcher = Matcher(
                db,
                umbral_titular=settings["matching"]["umbral_titular"],
                umbral_cuerpo=settings["matching"]["umbral_cuerpo"],
                ventana_horas=settings["matching"]["ventana_horas"],
            )
            total_matches = matcher.run()
            stats = db.get_stats()
            db.close()

            _run_status["last_result"] = {
                "articulos_nuevos": total_ingested,
                "matches_nuevos": total_matches,
                "stats": stats,
            }
        finally:
            _run_status["running"] = False

    threading.Thread(target=_run, daemon=True).start()
    return {"status": "started"}


@app.post("/api/run-full")
def run_full_cycle():
    if _run_status["running"]:
        return {"status": "already_running"}

    def _run():
        _run_status["running"] = True
        _run_status["last_result"] = None
        try:
            db = get_db()

            ingester = RSSIngester(db, user_agent=settings["ingesta"]["user_agent"])
            total_ingested = 0
            for medio_id, conf in feeds_config["medios"].items():
                total_ingested += ingester.ingest_medio(medio_id, conf["feeds"])

            matcher = Matcher(
                db,
                umbral_titular=settings["matching"]["umbral_titular"],
                umbral_cuerpo=settings["matching"]["umbral_cuerpo"],
                ventana_horas=settings["matching"]["ventana_horas"],
            )
            total_matches_p1 = matcher.run()

            from .scraping import ArticleScraper

            agencia = settings.get("scraping", {}).get("agencia", "europa press")
            delay = settings.get("scraping", {}).get("delay", 1.0)
            scraper = ArticleScraper(db, agencia=agencia, delay=delay)
            scrape_stats = scraper.scrape_pendientes(limit=50)

            keywords = settings.get("scraping", {}).get("agencia_keywords", [agencia])
            total_matches_p2 = matcher.run_deep(agencia_keywords=keywords)

            stats = db.get_stats()
            db.close()

            _run_status["last_result"] = {
                "articulos_nuevos": total_ingested,
                "matches_pase1": total_matches_p1,
                "scrapeados": scrape_stats["scrapeados"],
                "matches_pase2": total_matches_p2,
                "stats": stats,
            }
        finally:
            _run_status["running"] = False

    threading.Thread(target=_run, daemon=True).start()
    return {"status": "started"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
