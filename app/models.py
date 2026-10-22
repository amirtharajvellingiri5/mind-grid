from datetime import date

from pydantic import BaseModel, Field


class Document(BaseModel):
    id: str
    title: str
    source_url: str | None = None
    doc_type: str = "regulation"
    valid_from: date | None = None
    valid_to: date | None = None
    access_label: str = "public"


class Chunk(BaseModel):
    id: str
    document_id: str
    seq: int
    text: str
    section: str | None = None
    char_start: int
    char_end: int


class RetrievedChunk(Chunk):
    score: float


class Citation(BaseModel):
    marker: int            # the [n] the model used
    chunk_id: str
    document_id: str
    snippet: str


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class Answer(BaseModel):
    question: str
    answer: str
    citations: list[Citation]
    retrieved: list[RetrievedChunk]
    model: str
    latency_ms: int