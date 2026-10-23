import json
import os
import subprocess
import sys
import tempfile
import unittest

from app.config.defaults import DEFAULTS
from app.config.errors import ConfigError
from app.config.loader import load


class HiddenConfig(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump({"db": {"host": "file-host", "port": 1111}, "log": {"level": "warn"}}, f)

    def tearDown(self):
        os.unlink(self.path)

    def test_env_types_and_precedence(self):
        env = {"SHOPD__DB__PORT": "2222", "SHOPD__DB__SSL": "On", "SHOPD__db__pool__TIMEOUT": "0.75",
               "SHOPD__FEATURES": " search , export,beta ", "SHOPD__LOG__JSON": "0", "PATH": "/bin",
               "SHOPD_DB__PORT": "9", "OTHER__DB__PORT": "9", "SHOPD__NAME": "edge-1"}
        cfg = load(self.path, env=env)
        self.assertEqual(cfg["db"]["port"], 2222)
        self.assertIs(type(cfg["db"]["port"]), int)
        self.assertIs(cfg["db"]["ssl"], True)
        self.assertEqual(cfg["db"]["pool"], {"size": 5, "timeout": 0.75})
        self.assertEqual(cfg["db"]["host"], "file-host")
        self.assertEqual(cfg["features"], ["search", "export", "beta"])
        self.assertIs(cfg["log"]["json"], False)
        self.assertEqual(cfg["log"]["level"], "warn")
        self.assertEqual(cfg["name"], "edge-1")
        cfg = load(self.path, env=env, overrides=["db.port=3333", "log.level=debug", "features=", "db.ssl=NO"])
        self.assertEqual(cfg["db"]["port"], 3333)
        self.assertEqual(cfg["log"]["level"], "debug")
        self.assertEqual(cfg["features"], [])
        self.assertIs(cfg["db"]["ssl"], False)

    def test_bools(self):
        for s, want in [("1", True), ("TRUE", True), ("yes", True), ("on", True), ("0", False), ("False", False), ("off", False), ("No", False)]:
            self.assertIs(load(env={"SHOPD__LOG__JSON": s})["log"]["json"], want, s)

    def test_errors_name_the_setting(self):
        bad = [({"SHOPD__DB__PROT": "1"}, "db.prot"), ({"SHOPD__DB__PORT": "abc"}, "db.port"),
               ({"SHOPD__DB__PORT": "5.5"}, "db.port"), ({"SHOPD__DB__SSL": "maybe"}, "db.ssl"),
               ({"SHOPD__DB": "x"}, "db"), ({"SHOPD__DB__POOL__TIMEOUT": "fast"}, "db.pool.timeout"),
               ({"SHOPD__LOG__LEVEL__X": "1"}, "log.level.x")]
        for env, key in bad:
            with self.assertRaises(ConfigError, msg=str(env)) as cm:
                load(env=env)
            self.assertIn(key, str(cm.exception), env)
        for ov, key in [("db.pool=3", "db.pool"), ("nope.x=1", "nope.x"), ("db.pool.size=many", "db.pool.size")]:
            with self.assertRaises(ConfigError) as cm:
                load(env={}, overrides=[ov])
            self.assertIn(key, str(cm.exception))

    def test_defaults_untouched(self):
        before = json.dumps(DEFAULTS, sort_keys=True)
        load(self.path, env={"SHOPD__FEATURES": "a,b", "SHOPD__DB__POOL__SIZE": "9"}, overrides=["db.host=z"])
        self.assertEqual(json.dumps(DEFAULTS, sort_keys=True), before)
        self.assertEqual(load(env={})["db"]["pool"]["size"], 5)

    def test_environ_default(self):
        os.environ["SHOPD__DB__PORT"] = "4444"
        try:
            self.assertEqual(load()["db"]["port"], 4444)
        finally:
            del os.environ["SHOPD__DB__PORT"]

    def test_cli(self):
        env = dict(os.environ, SHOPD__DB__PORT="5555", SHOPD__LOG__LEVEL="error")
        r = subprocess.run([sys.executable, "-m", "app.config", "--file", self.path, "--set", "log.level=trace",
                            "--set", "db.pool.size=7"], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        cfg = json.loads(r.stdout)
        self.assertEqual((cfg["db"]["port"], cfg["log"]["level"], cfg["db"]["pool"]["size"]), (5555, "trace", 7))
        r = subprocess.run([sys.executable, "-m", "app.config", "--set", "db.prot=1"], capture_output=True, text=True,
                           env=dict(os.environ))
        self.assertEqual(r.returncode, 2)
        self.assertIn("db.prot", r.stderr)


if __name__ == "__main__":
    unittest.main()
