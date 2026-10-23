import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgres://localhost/orders_dev")
TAX_RATE = 0.08
