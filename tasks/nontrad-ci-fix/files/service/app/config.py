import importlib
import os


def load_settings():
    name = os.environ["APP_SETTINGS"]
    return importlib.import_module(f"app.settings_{name}")
