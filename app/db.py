import sqlite3
from typing import List, Tuple, Optional, Iterable
import contextlib
from pathlib import Path
import numpy as np

from .config import settings

DB_PATH = Path(settings.sqlite_path)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db() -> None:
    with contextlib.closing(get_conn()) as conn, conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            title TEXT,
            content TEXT NOT NULL,
            fetched_at TEXT NOT NULL
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            embedding BLOB NOT NULL,
            FOREIGN KEY(document_id) REFERENCES documents(id)
        );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id);")


def insert_document(url: str, title: str, content: str, fetched_at: str) -> int:
    with contextlib.closing(get_conn()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO documents(url, title, content, fetched_at) VALUES (?,?,?,?)",
            (url, title, content, fetched_at)
        )
        return cur.lastrowid


def insert_chunks(document_id: int, rows: List[Tuple[int, str, bytes]]) -> None:
    with contextlib.closing(get_conn()) as conn, conn:
        conn.executemany(
            "INSERT INTO chunks(document_id, chunk_index, text, embedding) VALUES (?,?,?,?)",
            [(document_id, idx, text, emb) for idx, text, emb in rows]
        )


def fetch_top_k_by_embedding(query_emb: Iterable[float], k: int) -> List[Tuple[int, int, str, str, Optional[str]]]:
    q = np.array(list(query_emb), dtype="float32")
    qn = np.linalg.norm(q) or 1.0

    with contextlib.closing(get_conn()) as conn:
        cur = conn.execute("""
            SELECT c.id, c.document_id, c.text, c.embedding, d.url, d.title
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
        """)
        rows = cur.fetchall()

    scored: List[Tuple[float, int, int, str, str, Optional[str]]] = []
    for cid, did, text, emb_blob, url, title in rows:
        vec = np.frombuffer(emb_blob, dtype="float32")
        if vec.size != q.size:
            continue
        denom = (np.linalg.norm(vec) * qn) or 1.0
        score = float(np.dot(vec, q) / denom)
        scored.append((score, cid, did, text, url, title))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:k]
    return [(cid, did, text, url, title) for (score, cid, did, text, url, title) in top]


def list_documents() -> List[Tuple[int, str, Optional[str]]]:
    with contextlib.closing(get_conn()) as conn:
        return list(conn.execute("SELECT id, url, title FROM documents ORDER BY id DESC"))
