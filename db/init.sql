CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id            TEXT PRIMARY KEY,               -- e.g. CELEX number
    title         TEXT NOT NULL,
    source_url    TEXT,
    doc_type      TEXT NOT NULL DEFAULT 'regulation',
    valid_from    DATE,
    valid_to      DATE,
    access_label  TEXT NOT NULL DEFAULT 'public',
    ingested_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE chunks (
    id           TEXT PRIMARY KEY,                -- "<document_id>:<seq>"
    document_id  TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    seq          INT  NOT NULL,
    text         TEXT NOT NULL,
    section      TEXT,
    char_start   INT  NOT NULL,
    char_end     INT  NOT NULL,
    embedding    vector(384) NOT NULL,
    UNIQUE (document_id, seq)
);

CREATE INDEX chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops);