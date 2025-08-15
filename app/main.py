from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, Response

from .config import settings
from .db import init_db, list_documents
from .webui import router as web_router
from .ingest import ingest_urls
from .rag import answer
from .schemas import IngestRequest, AskRequest, AskResponse, DocListItem

app = FastAPI(title="EORA RAG Assistant", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(web_router, prefix="/ui")

@app.on_event("startup")
def _startup():
    init_db()

@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/ui/")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ingest")
async def ingest(req: IngestRequest):
    urls = req.urls or settings.seed_links
    ids = await ingest_urls([str(u) for u in urls])
    return {"indexed_documents": ids, "count": len(ids)}

@app.get("/docs")
def docs_list() -> list[DocListItem]:
    rows = list_documents()
    return [DocListItem(id=i, url=u, title=t) for (i, u, t) in rows]

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    ans, srcs = answer(req.question, req.mode, req.top_k)
    return AskResponse(answer=ans, sources=srcs)
