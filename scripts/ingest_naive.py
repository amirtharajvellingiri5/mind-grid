import json
import re
from pathlib import Path

import psycopg
from bs4 import BeautifulSoup
from opentelemetry import trace
from pgvector.psycopg import register_vector

from app.config import settings
from app.embeddings import embed_passages
from app.tracing import setup_tracing

RAW = Path("data/raw")
CHUNK_SIZE, OVERLAP = 1200, 200


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    text = soup.get_text("\n")
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def chunk_fixed(text: str, size: int = CHUNK_SIZE, overlap: int = OVERLAP):
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        yield start, end, text[start:end]
        if end == len(text):
            break
        start = end - overlap


def main() -> None:
    provider = setup_tracing("gridmind-ingest")
    tracer = trace.get_tracer(__name__)
    manifest = json.loads((RAW / "manifest.json").read_text(encoding="utf-8"))

    with psycopg.connect(settings.database_url) as conn:
        register_vector(conn)
        for celex, meta in manifest.items():
            path = RAW / f"{celex}.html"
            if not path.exists():
                print(f"missing {path}, skipping")
                continue
            with tracer.start_as_current_span("ingest.document") as span:
                span.set_attribute("document.id", celex)
                text = html_to_text(path.read_text(encoding="utf-8"))
                pieces = list(chunk_fixed(text))
                vectors = embed_passages([p[2] for p in pieces])
                span.set_attribute("chunk.count", len(pieces))

                conn.execute(
                    """INSERT INTO documents (id, title, source_url)
                       VALUES (%s, %s, %s)
                       ON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title,
                           source_url = EXCLUDED.source_url, ingested_at = now()""",
                    (celex, meta["title"], meta["source_url"]),
                )
                conn.execute("DELETE FROM chunks WHERE document_id = %s", (celex,))
                with conn.cursor() as cur:
                    cur.executemany(
                        """INSERT INTO chunks (id, document_id, seq, text, char_start, char_end, embedding)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        [(f"{celex}:{i}", celex, i, chunk, s, e, vec)
                         for i, ((s, e, chunk), vec) in enumerate(zip(pieces, vectors))],
                    )
                conn.commit()
                print(f"{celex}: {len(text):,} chars -> {len(pieces)} chunks")

    provider.shutdown()


if __name__ == "__main__":
    main()