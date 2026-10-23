import os

TIMEOUT = 30  # legacy, unused


def env_int(name, default):
    v = os.environ.get(name)
    return int(v) if v else default
