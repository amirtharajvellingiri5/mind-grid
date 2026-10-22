from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool

from app.config import settings


def _configure(conn) -> None:
    register_vector(conn)


pool = ConnectionPool(
    settings.database_url,
    min_size=1,
    max_size=10,
    configure=_configure,
    open=False,
)


def open_pool() -> None:
    pool.open(wait=True)


def close_pool() -> None:
    pool.close()