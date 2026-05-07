import requests
from bs4 import BeautifulSoup


class LightPage:
    """Minimal page wrapper matching the Scrapling API surface we use."""

    def __init__(self, soup: BeautifulSoup):
        self._soup = soup

    def css(self, selector: str):
        return LightSelection(self._soup.select(selector.replace("::text", "")))

    def get_all_text(self) -> str:
        return self._soup.get_text(separator=" ", strip=True)


class LightSelection(list):
    def __init__(self, elements):
        super().__init__([LightElement(e) for e in elements])

    def get(self, default=None):
        if not self:
            return default
        return self[0].get_text()

    def getall(self):
        return [e.get_text() for e in self]

    def css(self, selector: str):
        results = []
        for el in self:
            results.extend(el._el.select(selector.replace("::text", "").strip() or "*"))
        if "::text" in selector:
            return LightTextResult([r.get_text(strip=True) for r in results])
        return LightSelection(results)


class LightTextResult(list):
    def get(self, default=None):
        return self[0] if self else default

    def getall(self):
        return list(self)


class LightElement:
    def __init__(self, el):
        self._el = el
        self.attrib = dict(el.attrs) if hasattr(el, "attrs") else {}

    def get_text(self):
        return self._el.get_text(strip=True) if hasattr(self._el, "get_text") else str(self._el)

    def css(self, selector: str):
        if "::text" in selector:
            clean = selector.replace("::text", "").strip()
            if clean:
                els = self._el.select(clean)
                return LightTextResult([e.get_text(strip=True) for e in els])
            return LightTextResult([self._el.get_text(strip=True)])
        return LightSelection(self._el.select(selector))


def fetch_page(url: str, timeout: int = 15):
    """Try Scrapling first, fall back to requests+BS4."""
    try:
        from scrapling.fetchers import Fetcher
        return Fetcher.get(url)
    except Exception:
        pass

    resp = requests.get(url, timeout=timeout, headers={
        "User-Agent": "Mozilla/5.0 (compatible; EPTrazabilidad/1.0)"
    })
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    return LightPage(soup)
