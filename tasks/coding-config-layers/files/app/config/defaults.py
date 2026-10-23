"""Built-in defaults. Every setting the service knows about is listed here."""

DEFAULTS = {
    "name": "shopd",
    "db": {
        "host": "localhost",
        "port": 5432,
        "ssl": False,
        "pool": {"size": 5, "timeout": 2.5},
    },
    "log": {"level": "info", "json": False},
    "features": ["search"],
}
