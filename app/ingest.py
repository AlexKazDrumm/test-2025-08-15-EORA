import asyncio
import datetime as dt
from typing import List, Sequence, Any
import httpx
import numpy as np

from .config import settings
from .db import init_db, insert_document, insert_chunks
from .utils import html_to_text, chunk_text
from .embeddings import get_embedder


async def fetch_url(client: httpx.AsyncClient, url: str) -> tuple[str, str]:
    r = await client.get(url, timeout=settings.timeout_seconds, headers={"User-Agent": settings.user_agent})
    r.raise_for_status()
    title, text = html_to_text(r.text)
    return title, text


def _urls_to_str_list(urls: Sequence[Any]) -> List[str]:
    return [str(u) for u in urls]


async def ingest_urls(urls: Sequence[Any]) -> List[int]:
    init_db()
    fetched_ids: List[int] = []
    urls_str = _urls_to_str_list(urls)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [fetch_url(client, u) for u in urls_str]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    embedder = get_embedder()

    for url, res in zip(urls_str, results):
        if isinstance(res, Exception):
            print(f"[WARN] skip {url}: {res}")
            continue

        title, text = res
        doc_id = insert_document(
            url=url,
            title=title,
            content=text,
            fetched_at=dt.datetime.utcnow().isoformat()
        )
        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            print(f"[WARN] empty content after chunking: {url}")
            continue

        try:
            vectors = embedder.embed_many(chunks)
        except Exception as e:
            print(f"[WARN] embeddings failed for {url} via {embedder.name}: {e}")
            continue

        rows = []
        for idx, (c, vec) in enumerate(zip(chunks, vectors)):
            arr = np.array(vec, dtype="float32")
            rows.append((idx, c, arr.tobytes()))
        insert_chunks(doc_id, rows)
        fetched_ids.append(doc_id)
        print(f"[OK] indexed {url} -> doc_id={doc_id}, chunks={len(chunks)} using {embedder.name}")

    return fetched_ids
