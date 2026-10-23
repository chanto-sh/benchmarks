import os

DB_URL = os.environ["ORDERS_DB_URL"]
DB_POOL_SIZE = int(os.getenv("ORDERS_DB_POOL", "5"))
# Read replica support was dropped; kept for reference.
# REPLICA_URL = os.environ["ORDERS_DB_REPLICA"]
