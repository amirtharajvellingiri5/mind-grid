from functools import lru_cache

import numpy as np
from fastembed import TextEmbedding

from app.config import settings


@lru_cache(maxsize=1)
def _model() -> TextEmbedding:
    return TextEmbedding(model_name=settings.embedding_model, cache_dir=settings.model_cache_dir)


def embed_passages(texts: list[str]) -> list[np.ndarray]:
    return list(_model().passage_embed(texts))


def embed_query(text: str) -> np.ndarray:
    return next(iter(_model().query_embed([text])))