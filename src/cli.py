import argparse
import csv
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

from .config import load_feeds, load_settings, PROJECT_ROOT
from .db import Database
from .ingesta import RSSIngester
from .matching import Matcher

console = Console()


def get_db(settings: dict) -> Database:
    db_path = PROJECT_ROOT / settings["db"]["path"]
    return Database(str(db_path))


def cmd_ingest(args, settings: dict, feeds_config: dict):
    db = get_db(settings)
    ingester = RSSIngester(db, user_agent=settings["ingesta"]["user_agent"])

    medios = feeds_config["medios"]
    if hasattr(args, "medio") and args.medio:
        medios = {k: v for k, v in medios.items() if k in args.medio}

    total = 0
    for medio_id, conf in medios.items():
        n = ingester.ingest_medio(medio_id, conf["feeds"])
        if n > 0:
            console.print(f"  [green]{conf['nombre']}[/]: {n} articulos nuevos")
        total += n

    console.print(f"\n[bold]Total: {total} articulos nuevos ingresados[/]")
    db.close()


def cmd_load_teletipos(args, settings: dict, feeds_config: dict):
    db = get_db(settings)
    path = Path(args.archivo)

    if path.suffix == ".csv":
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                db.insert_teletipo(
                    id=row["id"],
                    titular=row["titular"],
                    cuerpo=row.get("cuerpo", ""),
                    fecha_emision=row["fecha_emision"],
                    categoria=row.get("categoria"),
                )
                count += 1
        console.print(f"[green]{count} teletipos cargados desde {path.name}[/]")
    elif path.suffix == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for t in data:
            db.insert_teletipo(
                id=t["id"],
                titular=t["titular"],
                cuerpo=t.get("cuerpo", ""),
                fecha_emision=t["fecha_emision"],
                categoria=t.get("categoria"),
            )
        console.print(f"[green]{len(data)} teletipos cargados desde {path.name}[/]")
    else:
        console.print("[red]Formato no soportado. Usa .csv o .json[/]")
        sys.exit(1)

    db.close()


def cmd_match(args, settings: dict, feeds_config: dict):
    db = get_db(settings)
    matcher = Matcher(
        db,
        umbral_titular=settings["matching"]["umbral_titular"],
        umbral_cuerpo=settings["matching"]["umbral_cuerpo"],
        ventana_horas=settings["matching"]["ventana_horas"],
    )

    total = matcher.run()
    console.print(f"[bold green]{total} matches nuevos detectados (fuzzy titular)[/]")
    db.close()


def cmd_scrape(args, settings: dict, feeds_config: dict):
    from .scraping import ArticleScraper

    db = get_db(settings)
    agencia = settings.get("scraping", {}).get("agencia", "europa press")
    delay = settings.get("scraping", {}).get("delay", 1.0)
    limit = args.limit if hasattr(args, "limit") and args.limit else 50

    scraper = ArticleScraper(db, agencia=agencia, delay=delay)

    console.print(f"[bold]Scrapeando hasta {limit} articulos sin match (Scrapling)...[/]")
    stats = scraper.scrape_pendientes(limit=limit)

    console.print(f"  Scrapeados: [green]{stats['scrapeados']}[/]")
    console.print(f"  Errores:    [red]{stats['errores']}[/]")
    console.print(f"  Fuente directa detectada: [cyan]{stats['fuente_directa']}[/]")
    db.close()


def cmd_deep_match(args, settings: dict, feeds_config: dict):
    db = get_db(settings)
    agencia = settings.get("scraping", {}).get("agencia", "europa press")
    keywords = settings.get("scraping", {}).get("agencia_keywords", [agencia])

    matcher = Matcher(
        db,
        umbral_titular=settings["matching"]["umbral_titular"],
        umbral_cuerpo=settings["matching"]["umbral_cuerpo"],
        ventana_horas=settings["matching"]["ventana_horas"],
    )

    total = matcher.run_deep(agencia_keywords=keywords)
    console.print(f"[bold green]{total} matches nuevos detectados (deep matching)[/]")
    db.close()


def cmd_report(args, settings: dict, feeds_config: dict):
    db = get_db(settings)
    min_score = args.min_score if args.min_score else settings["matching"]["umbral_titular"]
    matches = db.get_matches(min_score=min_score)

    if not matches:
        console.print("[yellow]No hay matches registrados[/]")
        db.close()
        return

    if args.format == "table":
        table = Table(title="Matches detectados")
        table.add_column("Teletipo", style="cyan", max_width=40)
        table.add_column("Medio", style="green")
        table.add_column("Articulo", max_width=40)
        table.add_column("Score", justify="right")
        table.add_column("Metodo", style="magenta")
        table.add_column("Fecha pub.")
        table.add_column("URL", max_width=50)

        for m in matches:
            table.add_row(
                m["teletipo_titular"][:40],
                m["medio"],
                m["articulo_titular"][:40],
                f"{m['score_titular']:.0f}",
                m["metodo"],
                str(m["fecha_publicacion"] or "")[:16],
                m["url"],
            )
        console.print(table)
    elif args.format == "json":
        result = [dict(m) for m in matches]
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    elif args.format == "csv":
        writer = csv.writer(sys.stdout)
        writer.writerow(["teletipo_id", "teletipo_titular", "medio", "articulo_titular", "score_titular", "metodo", "fecha_publicacion", "url"])
        for m in matches:
            writer.writerow([m["teletipo_id"], m["teletipo_titular"], m["medio"], m["articulo_titular"], m["score_titular"], m["metodo"], m["fecha_publicacion"], m["url"]])

    db.close()


def cmd_stats(args, settings: dict, feeds_config: dict):
    db = get_db(settings)
    stats = db.get_stats()

    table = Table(title="Estado de la base de datos")
    table.add_column("Metrica", style="cyan")
    table.add_column("Valor", justify="right", style="green")
    table.add_row("Teletipos cargados", str(stats["teletipos"]))
    table.add_row("Articulos ingestados", str(stats["articulos"]))
    table.add_row("Articulos scrapeados", str(stats["scrapeados"]))
    table.add_row("Matches detectados", str(stats["matches"]))
    table.add_row("Medios con articulos", str(stats["medios"]))

    if stats["matches_por_metodo"]:
        console.print(table)
        console.print()
        table2 = Table(title="Matches por metodo")
        table2.add_column("Metodo", style="magenta")
        table2.add_column("Count", justify="right", style="green")
        for metodo, count in stats["matches_por_metodo"].items():
            table2.add_row(metodo, str(count))
        console.print(table2)
    else:
        console.print(table)

    db.close()


def cmd_run(args, settings: dict, feeds_config: dict):
    console.print("[bold]1/2 Ingresando articulos (RSS)...[/]")
    cmd_ingest(args, settings, feeds_config)
    console.print("\n[bold]2/2 Matching por titular...[/]")
    cmd_match(args, settings, feeds_config)
    console.print()
    cmd_stats(args, settings, feeds_config)


def cmd_run_full(args, settings: dict, feeds_config: dict):
    console.print("[bold]1/4 Ingresando articulos (RSS + feedparser)...[/]")
    cmd_ingest(args, settings, feeds_config)

    console.print("\n[bold]2/4 Matching por titular (RapidFuzz)...[/]")
    cmd_match(args, settings, feeds_config)

    console.print("\n[bold]3/4 Scrapeando articulos sin match (Scrapling)...[/]")
    cmd_scrape(args, settings, feeds_config)

    console.print("\n[bold]4/4 Deep matching (cuerpo + fuente)...[/]")
    cmd_deep_match(args, settings, feeds_config)

    console.print()
    cmd_stats(args, settings, feeds_config)


def main():
    parser = argparse.ArgumentParser(description="EP Trazabilidad - Sistema de trazabilidad de teletipos")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="Ingestar articulos de medios via RSS (feedparser)")
    p_ingest.add_argument("--medio", nargs="+", help="Solo estos medios (ids del config)")

    p_load = sub.add_parser("load", help="Cargar teletipos desde CSV o JSON")
    p_load.add_argument("archivo", help="Ruta al archivo CSV o JSON")

    p_match = sub.add_parser("match", help="Pase 1: fuzzy matching por titular")

    p_scrape = sub.add_parser("scrape", help="Scrapear articulos sin match con Scrapling")
    p_scrape.add_argument("--limit", type=int, default=50, help="Max articulos a scrapear (default: 50)")

    p_deep = sub.add_parser("deep-match", help="Pase 2: matching por cuerpo completo + fuente")

    p_report = sub.add_parser("report", help="Generar reporte de matches")
    p_report.add_argument("--format", choices=["table", "json", "csv"], default="table")
    p_report.add_argument("--min-score", type=float, help="Score minimo para incluir")

    p_stats = sub.add_parser("stats", help="Mostrar estadisticas de la base de datos")

    p_run = sub.add_parser("run", help="Ciclo rapido: ingest + match (solo RSS)")
    p_run.add_argument("--medio", nargs="+", help="Solo estos medios")

    p_full = sub.add_parser("run-full", help="Ciclo completo: ingest + match + scrape + deep-match")
    p_full.add_argument("--medio", nargs="+", help="Solo estos medios")
    p_full.add_argument("--limit", type=int, default=50, help="Max articulos a scrapear")

    args = parser.parse_args()
    settings = load_settings()
    feeds_config = load_feeds()

    commands = {
        "ingest": cmd_ingest,
        "load": cmd_load_teletipos,
        "match": cmd_match,
        "scrape": cmd_scrape,
        "deep-match": cmd_deep_match,
        "report": cmd_report,
        "stats": cmd_stats,
        "run": cmd_run,
        "run-full": cmd_run_full,
    }
    commands[args.command](args, settings, feeds_config)


if __name__ == "__main__":
    main()
