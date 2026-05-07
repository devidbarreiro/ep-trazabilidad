from datetime import datetime
from rapidfuzz import fuzz
from ..db import Database


class Matcher:
    def __init__(self, db: Database, umbral_titular: float = 80, umbral_cuerpo: float = 70, ventana_horas: int = 48):
        self.db = db
        self.umbral_titular = umbral_titular
        self.umbral_cuerpo = umbral_cuerpo
        self.ventana_horas = ventana_horas

    def match_articulo(self, articulo: dict) -> list[dict]:
        fecha = articulo["fecha_publicacion"] or datetime.now().isoformat()
        candidatos = self.db.get_teletipos_en_ventana(fecha, self.ventana_horas)

        resultados = []
        for teletipo in candidatos:
            score_titular = fuzz.partial_ratio(
                _normalizar(articulo["titular"]),
                _normalizar(teletipo["titular"]),
            )

            if score_titular < self.umbral_titular:
                continue

            score_cuerpo = None
            if articulo.get("resumen") and teletipo["cuerpo"]:
                score_cuerpo = fuzz.token_sort_ratio(
                    _normalizar(articulo["resumen"][:500]),
                    _normalizar(teletipo["cuerpo"][:500]),
                )

            resultados.append({
                "teletipo_id": teletipo["id"],
                "teletipo_titular": teletipo["titular"],
                "score_titular": score_titular,
                "score_cuerpo": score_cuerpo,
                "metodo": "fuzzy",
            })

        return resultados

    def match_deep(self, articulo: dict, agencia_keywords: list[str] | None = None) -> list[dict]:
        """Segundo pase: usa cuerpo completo y autor de scraping."""
        if agencia_keywords is None:
            agencia_keywords = ["europa press"]

        fecha = articulo["fecha_publicacion"] or datetime.now().isoformat()
        candidatos = self.db.get_teletipos_en_ventana(fecha, self.ventana_horas)
        if not candidatos:
            return []

        autor = (articulo.get("autor") or "").lower()
        autor_es_agencia = any(kw in autor for kw in agencia_keywords)

        cuerpo = articulo.get("cuerpo_completo") or ""
        if not cuerpo and not autor_es_agencia:
            return []

        resultados = []
        for teletipo in candidatos:
            score_titular = fuzz.partial_ratio(
                _normalizar(articulo["titular"]),
                _normalizar(teletipo["titular"]),
            )

            score_cuerpo = None
            if teletipo["cuerpo"] and cuerpo:
                score_cuerpo = fuzz.partial_ratio(
                    _normalizar(teletipo["cuerpo"][:500]),
                    _normalizar(cuerpo[:2000]),
                )

            if autor_es_agencia:
                threshold = 50
                metodo = "fuente"
            else:
                threshold = self.umbral_cuerpo
                metodo = "scraping_fuzzy"

            best_score = max(score_titular, score_cuerpo or 0)
            if best_score < threshold:
                continue

            resultados.append({
                "teletipo_id": teletipo["id"],
                "teletipo_titular": teletipo["titular"],
                "score_titular": score_titular,
                "score_cuerpo": score_cuerpo,
                "metodo": metodo,
            })

        return resultados

    def run(self) -> int:
        """Pase 1: fuzzy matching por titular (RSS)."""
        articulos = self.db.get_articulos_sin_match()
        total_matches = 0

        for art in articulos:
            art_dict = dict(art)
            matches = self.match_articulo(art_dict)

            for m in matches:
                self.db.insert_match(
                    teletipo_id=m["teletipo_id"],
                    articulo_id=art["id"],
                    score_titular=m["score_titular"],
                    score_cuerpo=m["score_cuerpo"],
                    metodo=m["metodo"],
                )
                total_matches += 1

        return total_matches

    def run_deep(self, agencia_keywords: list[str] | None = None) -> int:
        """Pase 2: matching profundo con datos de scraping."""
        articulos = self.db.get_articulos_scrapeados_sin_match()
        total_matches = 0

        for art in articulos:
            art_dict = dict(art)
            matches = self.match_deep(art_dict, agencia_keywords)

            for m in matches:
                self.db.insert_match(
                    teletipo_id=m["teletipo_id"],
                    articulo_id=art["id"],
                    score_titular=m["score_titular"],
                    score_cuerpo=m["score_cuerpo"],
                    metodo=m["metodo"],
                )
                total_matches += 1

        return total_matches


def _normalizar(texto: str) -> str:
    return texto.lower().strip()
