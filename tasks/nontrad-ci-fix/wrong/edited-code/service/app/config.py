import importlib
import os


def load_settings():
    name = os.environ.get("APP_SETTINGS", "ci")
    return importlib.import_module(f"app.settings_{name}")
