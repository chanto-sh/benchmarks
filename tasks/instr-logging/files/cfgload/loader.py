import json

DEFAULTS = {"theme": "light", "retries": 3}


def load_config(path):
    with open(path) as f:
        data = json.load(f)
    return {**DEFAULTS, **data}
