"""Safe management for external RAG website source configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("knowledge_sources") / "web_sources.json"


def load_web_sources(config_path: str | Path = DEFAULT_CONFIG_PATH) -> list[dict]:
    """Load configured web sources, creating a safe empty config when missing."""
    path = Path(config_path)
    _ensure_config_file(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    raw_sources = payload.get("sources", []) if isinstance(payload, dict) else []
    if not isinstance(raw_sources, list):
        return []
    sources: list[dict] = []
    for source in raw_sources:
        if not isinstance(source, dict):
            continue
        url = str(source.get("url") or "").strip()
        if not _is_valid_url(url):
            continue
        sources.append(
            {
                "name": str(source.get("name") or url).strip() or url,
                "url": url,
                "enabled": bool(source.get("enabled", True)),
            }
        )
    return sources


def save_web_sources(
    sources: list[dict],
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> None:
    """Save valid web sources to JSON using the app's source format."""
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    clean_sources = []
    seen_urls: set[str] = set()
    for source in sources:
        url = str(source.get("url") or "").strip()
        if not _is_valid_url(url) or url in seen_urls:
            continue
        seen_urls.add(url)
        clean_sources.append(
            {
                "name": str(source.get("name") or url).strip() or url,
                "url": url,
                "enabled": bool(source.get("enabled", True)),
            }
        )
    path.write_text(
        json.dumps({"sources": clean_sources}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_web_source(
    name: str,
    url: str,
    enabled: bool = True,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> dict:
    """Add a valid unique web source and return the saved source dictionary."""
    cleaned_url = url.strip()
    if not _is_valid_url(cleaned_url):
        raise ValueError("Website URL must start with http:// or https://.")
    sources = load_web_sources(config_path)
    for source in sources:
        if source["url"] == cleaned_url:
            return source
    source = {
        "name": name.strip() or cleaned_url,
        "url": cleaned_url,
        "enabled": bool(enabled),
    }
    sources.append(source)
    save_web_sources(sources, config_path)
    return source


def remove_web_source(
    url: str,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> bool:
    """Remove a web source by URL and return whether anything changed."""
    cleaned_url = url.strip()
    sources = load_web_sources(config_path)
    remaining = [source for source in sources if source["url"] != cleaned_url]
    if len(remaining) == len(sources):
        return False
    save_web_sources(remaining, config_path)
    return True


def set_web_source_enabled(
    url: str,
    enabled: bool,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> bool:
    """Enable or disable a web source by URL."""
    cleaned_url = url.strip()
    sources = load_web_sources(config_path)
    changed = False
    for source in sources:
        if source["url"] == cleaned_url:
            source["enabled"] = bool(enabled)
            changed = True
            break
    if changed:
        save_web_sources(sources, config_path)
    return changed


def _ensure_config_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text('{"sources": []}', encoding="utf-8")


def _is_valid_url(url: str) -> bool:
    return url.startswith(("http://", "https://"))
