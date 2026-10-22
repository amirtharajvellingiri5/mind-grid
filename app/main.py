from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app import rag
from app.config import settings
from app.db import close_pool, open_pool, pool
from app.models import Answer, AskRequest
from app.tracing import setup_tracing

provider = setup_tracing("gridmind-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    open_pool()
    yield
    close_pool()
    provider.shutdown()


app = FastAPI(title="GridMind", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)


@app.get("/health")
def health() -> dict:
    with pool.connection() as conn:
        docs = conn.execute("SELECT count(*) FROM documents").fetchone()[0]
        chunks = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
    return {"status": "ok", "documents": docs, "chunks": chunks}


@app.post("/ask", response_model=Answer)
def ask(req: AskRequest) -> Answer:
    return rag.answer(req.question, req.top_k)