from pydantic import BaseModel, HttpUrl
from typing import List, Literal


class IngestRequest(BaseModel):
    urls: List[HttpUrl] | None = None


class AskRequest(BaseModel):
    question: str
    mode: Literal["simple","sources","inline","extractive"] = "inline"
    top_k: int | None = None


class AskResponse(BaseModel):
    answer: str
    sources: List[HttpUrl]


class DocListItem(BaseModel):
    id: int
    url: HttpUrl
    title: str | None
