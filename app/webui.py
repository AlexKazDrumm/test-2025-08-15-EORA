from typing import List, Optional
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from starlette.templating import Jinja2Templates
from io import BytesIO
from markdown import markdown  # NEW

from .config import settings
from .embeddings import reset_embedder
from .ingest import ingest_urls
from .rag import answer
from .db import list_documents
from .links import resolve_links

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def ui_index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "settings": settings,
        "docs": list_documents(),
        "answer": None,
        "answer_html": None,
        "sources": [],
        "last_mode": None,
        "message": None
    })


@router.post("/ingest", response_class=HTMLResponse)
async def ui_ingest(
    request: Request,
    embedding_backend: str = Form("local"),
    openai_api_key: Optional[str] = Form(None),
    openai_chat_model: str = Form("gpt-4o"),
    openai_embedding_model: str = Form("text-embedding-3-large"),
    custom_urls: str = Form(""),
    links_file: UploadFile | None = File(None),
):
    settings.openai_api_key = openai_api_key or None
    settings.openai_chat_model = openai_chat_model or settings.openai_chat_model
    settings.openai_embedding_model = openai_embedding_model or settings.openai_embedding_model
    reset_embedder(embedding_backend)

    file_text: Optional[str] = None
    if links_file is not None:
        raw = await links_file.read()
        try:
            file_text = raw.decode("utf-8")
        except UnicodeDecodeError:
            file_text = raw.decode("utf-8-sig", errors="ignore")

    urls: List[str] = resolve_links(
        custom_urls=[u.strip() for u in custom_urls.splitlines() if u.strip()] if custom_urls.strip() else None,
        file_text=file_text,
    )

    try:
        ids = await ingest_urls(urls)
        msg = f"Индексировано документов: {len(ids)}"
    except Exception as e:
        msg = f"Ошибка индексации: {e}"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "settings": settings,
        "docs": list_documents(),
        "answer": None,
        "answer_html": None,
        "sources": [],
        "last_mode": None,
        "message": msg
    })


@router.post("/ask", response_class=HTMLResponse)
async def ui_ask(
    request: Request,
    question: str = Form(...),
    mode: str = Form("inline"),
    top_k: int = Form(6),
    embedding_backend: str = Form("local"),
    openai_api_key: Optional[str] = Form(None),
    openai_chat_model: str = Form("gpt-4o"),
    openai_embedding_model: str = Form("text-embedding-3-large"),
):
    settings.openai_api_key = openai_api_key or None
    settings.openai_chat_model = openai_chat_model or settings.openai_chat_model
    settings.openai_embedding_model = openai_embedding_model or settings.openai_embedding_model
    reset_embedder(embedding_backend)

    text, srcs = answer(question, mode, top_k)
    html = markdown(text, extensions=["extra", "nl2br"])

    return templates.TemplateResponse("index.html", {
        "request": request,
        "settings": settings,
        "docs": list_documents(),
        "answer": text,
        "answer_html": html,
        "sources": srcs,
        "message": None,
        "last_question": question,
        "last_mode": mode,
        "last_top_k": top_k,
    })


@router.post("/export", response_class=StreamingResponse)
async def ui_export(
    answer_md: str = Form(...),
    filename: str = Form("answer.md"),
):
    data = answer_md.encode("utf-8")
    buf = BytesIO(data)
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(buf, media_type="text/markdown; charset=utf-8", headers=headers)
