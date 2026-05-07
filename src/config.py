from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).parent.parent


def load_feeds(path: str | None = None) -> dict:
    p = Path(path) if path else PROJECT_ROOT / "config" / "feeds.yaml"
    with open(p) as f:
        return yaml.safe_load(f)


def load_settings(path: str | None = None) -> dict:
    p = Path(path) if path else PROJECT_ROOT / "config" / "settings.yaml"
    with open(p) as f:
        return yaml.safe_load(f)
