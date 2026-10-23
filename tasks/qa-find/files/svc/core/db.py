from svc.core.settings import env_int

DB_TIMEOUT_S = env_int("SVC_DB_TIMEOUT", 10)
