from __future__ import annotations
from pathlib import Path
from typing import List, Sequence


def parse_links_text(text: str) -> List[str]:
    urls: List[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.lower().startswith(("http://", "https://")):
            urls.append(s)

    return dedup(urls)


def load_links_from_file(path: str | Path) -> List[str]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"links file not found: {p}")
    txt = p.read_text(encoding="utf-8-sig")
    return parse_links_text(txt)


def dedup(urls: Sequence[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def resolve_links(custom_urls: Sequence[str] | None = None, file_text: str | None = None) -> List[str]:
    if file_text:
        urls = parse_links_text(file_text)
        if urls:
            return urls

    if custom_urls:
        urls = [u.strip() for u in custom_urls if u and u.strip()]
        return dedup(urls)

    from .config import settings
    if settings.seed_links_file:
        try:
            return load_links_from_file(settings.seed_links_file)
        except FileNotFoundError:
            pass

    return [str(u) for u in settings.seed_links]
