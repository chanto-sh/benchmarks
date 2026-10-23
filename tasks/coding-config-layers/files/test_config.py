import json
import os
import tempfile
import unittest

from app.config.errors import ConfigError
from app.config.loader import load


class ConfigTest(unittest.TestCase):
    def test_defaults(self):
        cfg = load()
        self.assertEqual(cfg["db"]["port"], 5432)
        self.assertEqual(cfg["features"], ["search"])

    def test_file_layer(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"db": {"host": "db.internal", "pool": {"size": 20}}}, f)
        try:
            cfg = load(f.name)
        finally:
            os.unlink(f.name)
        self.assertEqual(cfg["db"]["host"], "db.internal")
        self.assertEqual(cfg["db"]["pool"], {"size": 20, "timeout": 2.5})
        self.assertEqual(cfg["db"]["port"], 5432)

    def test_bad_file(self):
        with self.assertRaises(ConfigError):
            load("/nonexistent/config.json")


if __name__ == "__main__":
    unittest.main()
