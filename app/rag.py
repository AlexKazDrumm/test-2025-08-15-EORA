from typing import List, Tuple, Literal, Optional
from dataclasses import dataclass
import re
import textwrap

from .config import settings
from .db import fetch_top_k_by_embedding
from .utils import make_inline_citations
from .embeddings import get_embedder

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


def _get_openai_client() -> Optional["OpenAI"]:
    if OpenAI is None or not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


@dataclass
class RetrievedChunk:
    chunk_id: int
    document_id: int
    text: str
    url: str
    title: Optional[str] = None


_PROJECT_KEYWORDS = [
    ("магнит", "Магнит"),
    ("kazanexpress", "KazanExpress"),
    ("lamoda", "Lamoda"),
    ("purina", "Purina"),
    ("qiwi", "QIWI"),
    ("dodo", "Dodo Pizza"),
    ("s7", "S7"),
    ("skolkovo", "Сколково"),
    ("ifarm", "iFarm"),
    ("sportrecs", "Sportrecs"),
    ("karcher", "Kärcher"),
    ("avon", "AVON"),
    ("skinclub", "SkinClub"),
    ("zeptolab", "ZeptoLab"),
    ("goosegaming", "Goose Gaming"),
]


def _extract_project_names(title: Optional[str], url: str) -> List[str]:
    s = ((title or "") + " " + url).lower()
    found: List[str] = []
    for key, canon in _PROJECT_KEYWORDS:
        if key in s:
            found.append(canon)
    return found


def _build_context(chunks: List[RetrievedChunk], max_chars: int) -> Tuple[str, List[Tuple[str, str]], List[List[str]]]:
    parts: List[str] = []
    refs: List[Tuple[str, str]] = []
    proj_map: List[List[str]] = []
    used = 0
    for i, ch in enumerate(chunks, start=1):
        header = ch.title.strip() if ch.title else ch.url
        part = f"[{i}] {header}\n{ch.url}\n{ch.text}\n"
        if used + len(part) > max_chars and i > 1:
            break
        parts.append(part)
        used += len(part)
        refs.append((f"[{i}]", ch.url))
        proj_map.append(_extract_project_names(ch.title, ch.url))
    return "\n---\n".join(parts), refs, proj_map


def _gen_via_openai(system: str, user: str) -> str:
    client = _get_openai_client()
    if client is None:
        raise RuntimeError("OpenAI client is not available")
    resp = client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.1,
        max_tokens=220,
    )
    return resp.choices[0].message.content.strip()


def _unique_keep_order(urls: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def gen_answer_simple(question: str, context: str) -> str:
    system = (
        "Ты помощник. Отвечай по-русски. Используй только Контекст. "
        "Ответ — 1–2 коротких предложения, без воды. "
        "Если в контексте есть названия проектов/брендов (Магнит, KazanExpress и т.п.) — обязательно упомяни их."
        "Используй 'Например', 'В числе', 'Среди', в вопросах, где требуется перечисление кейсов и тп."
    )
    user = f"Вопрос:\n{question}\n\nКонтекст:\n{context}\n\nОтветь без ссылок."
    return _gen_via_openai(system, user)


def gen_answer_with_sources(question: str, context: str) -> str:
    system = (
        "Ты помощник. Отвечай по-русски. Используй только Контекст. "
        "Ответ лаконичный: 1–2 предложения. В конце: 'Источники: [1], [2]'. "
        "Обязательно упоминай конкретные названия проектов/брендов, если они есть."
        "Используй 'Например', 'В числе', 'Среди', в вопросах, где требуется перечисление кейсов и тп."
    )
    user = textwrap.dedent(f"""
    Вопрос:
    {question}

    Контекст:
    {context}
    """).strip()
    return _gen_via_openai(system, user)


def _force_inline_if_missing(text: str, refs: List[Tuple[str, str]], proj_map: List[List[str]]) -> str:
    out = text
    for idx, ((anchor, url), projects) in enumerate(zip(refs, proj_map), start=1):
        if (f"[\\[{idx}\\]](" in out) or (f"[{idx}](" in out):
            continue

        placed = False
        for proj in projects:
            pattern = re.compile(rf"({re.escape(proj)})", flags=re.IGNORECASE)
            new_out, n = pattern.subn(rf"\1 [\[{idx}\]]({url})", out, count=1)
            if n > 0:
                out = new_out
                placed = True
                break

        if not placed:
            out = re.sub(r'([.!?])', rf' [\[{idx}\]]({url})\1', out, count=1)

    for idx in range(1, len(refs) + 1):
        out = re.sub(rf"(?<!\w)\[{idx}\](?!\()", "", out)

    return out


def gen_answer_inline(question: str, context: str, refs: List[Tuple[str, str]], proj_map: List[List[str]]) -> str:
    hint_lines: List[str] = []
    for i, projects in enumerate(proj_map, start=1):
        if projects:
            hint_lines.append(f"[{i}] → {', '.join(sorted(set(projects)))}")
        else:
            hint_lines.append(f"[{i}] → (общая информация)")

    hints = "\n".join(hint_lines)

    system = (
        "Ты помощник. Отвечай по-русски. Используй только Контекст. "
        "Дай 1–2 коротких предложения. Впиши ссылки как [1], [2] строго в уместных местах; дублей одной и той же метки быть не должно. "
        "Используй 'Например', 'В числе', 'Среди', в вопросах, где требуется перечисление кейсов и тп."
        "Не добавляй строку 'Источники: ...' в конце. "
        "Если упоминаешь проекты/бренды — называй их явно."
    )
    user = textwrap.dedent(f"""
    Вопрос:
    {question}

    Контекст:
    {context}

    Подсказки по соответствию меток и проектов:
    {hints}
    """).strip()

    raw = _gen_via_openai(system, user)
    with_links = make_inline_citations(raw, refs)
    finalized = _force_inline_if_missing(with_links, refs, proj_map)
    for idx in range(1, len(refs) + 1):
        finalized = re.sub(rf"(?<!\w)\[{idx}\](?!\()", "", finalized)
    return finalized


def gen_answer_extractive(question: str, chunks: List[RetrievedChunk]) -> str:
    if not chunks:
        return "К сожалению, по вопросу не найдены релевантные фрагменты."
    max_snippets = min(3, len(chunks))
    parts: List[str] = []
    for i in range(max_snippets):
        ch = chunks[i]
        header = ch.title.strip() if ch.title else ch.url
        snippet = ch.text.strip()
        if len(snippet) > 300:
            snippet = snippet[:300].rsplit(" ", 1)[0] + "…"
        parts.append(f"• {header}: {snippet} [{i+1}]")
    lead = "Коротко по материалам:\n"
    return lead + "\n".join(parts)


def answer(
    question: str,
    mode: Literal["simple", "sources", "inline", "extractive"] = "inline",
    top_k: int | None = None
) -> Tuple[str, List[str]]:
    k = top_k or settings.top_k
    embedder = get_embedder()
    q_emb = embedder.embed_one(question)
    rows = fetch_top_k_by_embedding(q_emb, k)
    chunks = [RetrievedChunk(chunk_id=cid, document_id=did, text=text, url=url, title=title) for (cid, did, text, url, title) in rows]

    context, refs, proj_map = _build_context(chunks, settings.max_context_chars)

    try:
        if mode == "simple":
            text = gen_answer_simple(question, context)
        elif mode == "sources":
            text = gen_answer_with_sources(question, context)
        elif mode == "inline":
            text = gen_answer_inline(question, context, refs, proj_map)
        else:
            text = gen_answer_extractive(question, chunks)
    except Exception as e:
        text = gen_answer_extractive(question, chunks) + f"\n\n_Примечание: генерация через OpenAI недоступна ({e}). Показан офлайн-ответ._"

    used_urls = _unique_keep_order([u for (_, u) in refs])
    return text, used_urls
