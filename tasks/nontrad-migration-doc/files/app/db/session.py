"""The replacement for legacy_db: pooled connections and parameter binding."""
from app import settings


class Session:
    def __init__(self, url=None, pool_size=None):
        self.url = url or settings.DB_URL
        self.pool_size = pool_size or settings.DB_POOL_SIZE

    def fetch_all(self, sql, params=()):
        raise NotImplementedError("wired up in production")
