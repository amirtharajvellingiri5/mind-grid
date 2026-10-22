import re
import time

from opentelemetry import trace
from psycopg.rows import dict_row

from app.config import settings
from app.db import pool
from app.embeddings import embed_query
from app.llm import complete
from app.models import Answer, Citation, RetrievedChunk

tracer = trace.get_tracer(__name__)

SYSTEM_PROMPT = """You answer questions about EU energy-market regulation using ONLY the numbered sources provided.
Cite every claim with its source number in square brackets, like [2].
If the sources do not contain the answer, reply exactly: "I can't answer that from the indexed documents." and cite nothing."""


def retrieve(question: str, k: int) -> list[RetrievedChunk]:
    with tracer.start_as_current_span("retrieve") as span:
        span.set_attribute("openinference.span.kind", "RETRIEVER")
        span.set_attribute("input.value", question)

        qvec = embed_query(question)
        with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, document_id, seq, text, section, char_start, char_end,
                       1 - (embedding <=> %(q)s) AS score
                FROM chunks
                ORDER BY embedding <=> %(q)s
                LIMIT %(k)s
                """,
                {"q": qvec, "k": k},
            )
            chunks = [RetrievedChunk(**row) for row in cur.fetchall()]

        for i, c in enumerate(chunks):
            span.set_attribute(f"retrieval.documents.{i}.document.id", c.id)
            span.set_attribute(f"retrieval.documents.{i}.document.score", c.score)
            span.set_attribute(f"retrieval.documents.{i}.document.content", c.text)
        return chunks


def build_context(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(
        f"[{i}] (document {c.document_id}, chunk {c.seq})\n{c.text}"
        for i, c in enumerate(chunks, start=1)
    )


def extract_citations(text: str, chunks: list[RetrievedChunk]) -> list[Citation]:
    markers = sorted({int(m) for m in re.findall(r"\[(\d+)\]", text)})
    return [
        Citation(
            marker=m,
            chunk_id=chunks[m - 1].id,
            document_id=chunks[m - 1].document_id,
            snippet=chunks[m - 1].text[:200],
        )
        for m in markers
        if 1 <= m <= len(chunks)
    ]


def answer(question: str, k: int | None = None) -> Answer:
    k = k or settings.top_k
    with tracer.start_as_current_span("rag.answer") as span:
        span.set_attribute("openinference.span.kind", "CHAIN")
        span.set_attribute("input.value", question)
        t0 = time.perf_counter()

        chunks = retrieve(question, k)
        user_msg = f"Sources:\n{build_context(chunks)}\n\nQuestion: {question}"
        text, model = complete(SYSTEM_PROMPT, user_msg)
        citations = extract_citations(text, chunks)

        span.set_attribute("output.value", text)
        return Answer(
            question=question,
            answer=text,
            citations=citations,
            retrieved=chunks,
            model=model,
            latency_ms=int((time.perf_counter() - t0) * 1000),
        )