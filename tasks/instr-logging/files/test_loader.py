import json, os, tempfile, unittest

from cfgload import load_config


class LoaderTest(unittest.TestCase):
    def test_merges_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "c.json")
            with open(p, "w") as f:
                json.dump({"theme": "dark"}, f)
            self.assertEqual(load_config(p), {"theme": "dark", "retries": 3})


if __name__ == "__main__":
    unittest.main()
