import sqlite3
from pathlib import Path
from datetime import datetime


class Database:
    def __init__(self, db_path: str = "data/trazabilidad.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()
        self._migrate()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS teletipos (
                id TEXT PRIMARY KEY,
                titular TEXT NOT NULL,
                cuerpo TEXT,
                fecha_emision DATETIME NOT NULL,
                categoria TEXT
            );

            CREATE TABLE IF NOT EXISTS articulos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medio TEXT NOT NULL,
                seccion TEXT,
                titular TEXT NOT NULL,
                resumen TEXT,
                url TEXT UNIQUE NOT NULL,
                fecha_publicacion DATETIME,
                fecha_ingesta DATETIME DEFAULT CURRENT_TIMESTAMP,
                autor TEXT,
                cuerpo_completo TEXT,
                scrapeado INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teletipo_id TEXT REFERENCES teletipos(id),
                articulo_id INTEGER REFERENCES articulos(id),
                score_titular REAL NOT NULL,
                score_cuerpo REAL,
                metodo TEXT DEFAULT 'fuzzy',
                fecha_deteccion DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(teletipo_id, articulo_id)
            );

            CREATE INDEX IF NOT EXISTS idx_articulos_medio ON articulos(medio);
            CREATE INDEX IF NOT EXISTS idx_articulos_fecha ON articulos(fecha_publicacion);
            CREATE INDEX IF NOT EXISTS idx_teletipos_fecha ON teletipos(fecha_emision);
            CREATE INDEX IF NOT EXISTS idx_matches_teletipo ON matches(teletipo_id);
        """)

    def _migrate(self):
        cols = {row[1] for row in self.conn.execute("PRAGMA table_info(articulos)").fetchall()}
        for col, typedef in [("autor", "TEXT"), ("cuerpo_completo", "TEXT"), ("scrapeado", "INTEGER DEFAULT 0")]:
            if col not in cols:
                self.conn.execute(f"ALTER TABLE articulos ADD COLUMN {col} {typedef}")
        self.conn.commit()

    def insert_teletipo(self, id: str, titular: str, cuerpo: str | None, fecha_emision: str, categoria: str | None = None):
        self.conn.execute(
            "INSERT OR IGNORE INTO teletipos (id, titular, cuerpo, fecha_emision, categoria) VALUES (?, ?, ?, ?, ?)",
            (id, titular, cuerpo, fecha_emision, categoria),
        )
        self.conn.commit()

    def insert_articulo(self, medio: str, seccion: str | None, titular: str, resumen: str | None, url: str, fecha_publicacion: str | None) -> int | None:
        try:
            cursor = self.conn.execute(
                "INSERT INTO articulos (medio, seccion, titular, resumen, url, fecha_publicacion) VALUES (?, ?, ?, ?, ?, ?)",
                (medio, seccion, titular, resumen, url, fecha_publicacion),
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def update_articulo_scraping(self, articulo_id: int, autor: str | None, cuerpo_completo: str | None):
        self.conn.execute(
            "UPDATE articulos SET autor = ?, cuerpo_completo = ?, scrapeado = 1 WHERE id = ?",
            (autor, cuerpo_completo, articulo_id),
        )
        self.conn.commit()

    def insert_match(self, teletipo_id: str, articulo_id: int, score_titular: float, score_cuerpo: float | None = None, metodo: str = "fuzzy"):
        self.conn.execute(
            "INSERT OR IGNORE INTO matches (teletipo_id, articulo_id, score_titular, score_cuerpo, metodo) VALUES (?, ?, ?, ?, ?)",
            (teletipo_id, articulo_id, score_titular, score_cuerpo, metodo),
        )
        self.conn.commit()

    def get_teletipos_en_ventana(self, fecha: str, ventana_horas: int = 48) -> list[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT * FROM teletipos
            WHERE fecha_emision BETWEEN datetime(?, '-' || ? || ' hours') AND datetime(?, '+' || ? || ' hours')
            """,
            (fecha, ventana_horas, fecha, ventana_horas),
        ).fetchall()

    def get_articulos_sin_match(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT a.* FROM articulos a
            LEFT JOIN matches m ON a.id = m.articulo_id
            WHERE m.id IS NULL
            """,
        ).fetchall()

    def get_articulos_sin_match_no_scrapeados(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT a.* FROM articulos a
            LEFT JOIN matches m ON a.id = m.articulo_id
            WHERE m.id IS NULL AND a.scrapeado = 0
            """,
        ).fetchall()

    def get_articulos_scrapeados_sin_match(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT a.* FROM articulos a
            LEFT JOIN matches m ON a.id = m.articulo_id
            WHERE m.id IS NULL AND a.scrapeado = 1
            """,
        ).fetchall()

    def get_matches(self, min_score: float = 0) -> list[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT m.*, t.titular as teletipo_titular, a.titular as articulo_titular,
                   a.medio, a.url, a.fecha_publicacion, t.fecha_emision
            FROM matches m
            JOIN teletipos t ON m.teletipo_id = t.id
            JOIN articulos a ON m.articulo_id = a.id
            WHERE MAX(m.score_titular, COALESCE(m.score_cuerpo, 0)) >= ?
            ORDER BY m.fecha_deteccion DESC
            """,
            (min_score,),
        ).fetchall()

    def get_stats(self) -> dict:
        teletipos = self.conn.execute("SELECT COUNT(*) FROM teletipos").fetchone()[0]
        articulos = self.conn.execute("SELECT COUNT(*) FROM articulos").fetchone()[0]
        matches = self.conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        medios = self.conn.execute("SELECT COUNT(DISTINCT medio) FROM articulos").fetchone()[0]
        scrapeados = self.conn.execute("SELECT COUNT(*) FROM articulos WHERE scrapeado = 1").fetchone()[0]
        matches_por_metodo = {}
        for row in self.conn.execute("SELECT metodo, COUNT(*) as n FROM matches GROUP BY metodo").fetchall():
            matches_por_metodo[row["metodo"]] = row["n"]
        return {
            "teletipos": teletipos,
            "articulos": articulos,
            "matches": matches,
            "medios": medios,
            "scrapeados": scrapeados,
            "matches_por_metodo": matches_por_metodo,
        }

    def close(self):
        self.conn.close()
