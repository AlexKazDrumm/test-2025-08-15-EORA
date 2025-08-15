import re
from bs4 import BeautifulSoup
from typing import Tuple, List


def _strip_noise(text: str) -> str:
    lines = text.splitlines()
    out: List[str] = []
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        if '"lid"' in s or "li_name" in s or "li_type" in s or "li_parent_id" in s:
            continue
        if (s.count("{") + s.count("}") + s.count("[") + s.count("]") + s.count(":") + s.count('"')) >= 10 and len(s) > 120:
            continue
        if s in ("О компании", "Услуги", "Портфолио", "Блог", "Вакансии", "Контакты", "+7 495 414-40-49", "Получить консультацию"):
            continue
        out.append(s)
    return "\n".join(out)


def html_to_text(html: str) -> Tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = soup.title.get_text(strip=True) if soup.title else ""
    text = soup.get_text(separator="\n")
    text = re.sub(r"\n{2,}", "\n\n", text).strip()
    text = _strip_noise(text)
    return title, text


def chunk_text(text: str, chunk_size_words: int, overlap_words: int) -> List[str]:
    if chunk_size_words <= overlap_words:
        raise ValueError("chunk_size must be greater than overlap")
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(len(words), start + chunk_size_words)
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start = end - overlap_words
    return chunks


def _strip_sources_sections(s: str) -> str:
    lines = s.splitlines()
    cleaned: List[str] = []
    for ln in lines:
        ln_stripped = ln.strip()
        if ln_stripped.lower().startswith("источники:") or ln_stripped.lower().startswith("sources:"):
            continue
        cleaned.append(ln)
    return "\n".join(cleaned).strip()


def _tidy_spaces(s: str) -> str:
    s = re.sub(r"\s+([.,;:!?])", r"\1", s)
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()


def make_inline_citations(answer: str, refs: List[tuple[str, str]]) -> str:
    import re as _re
    s = _strip_sources_sections(answer)

    for anchor, url in refs:
        n = anchor.strip("[]")
        bare = _re.compile(rf"(?<!\w)\[{_re.escape(n)}\](?!\()")
        already_linked_token_plain = f"[{n}]("
        already_linked_token_bracketed = f"[\\[{n}\\]]("

        if (already_linked_token_plain in s) or (already_linked_token_bracketed in s):
            s = bare.sub("", s)
            continue

        s, _ = bare.subn(f"[\\[{n}\\]]({url})", s, count=1)

        s = bare.sub("", s)

    return _tidy_spaces(s)
