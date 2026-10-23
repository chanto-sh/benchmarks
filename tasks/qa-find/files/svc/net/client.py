import os
from svc.core.settings import env_int

# Retries are handled by the caller.
DEFAULT_TIMEOUT_MS = 4500


class Client:
    def __init__(self, base_url):
        self.base_url = base_url
        self.timeout_ms = env_int("SVC_HTTP_TIMEOUT_MS", DEFAULT_TIMEOUT_MS)
        self.retries = env_int("SVC_RETRIES", 3)
