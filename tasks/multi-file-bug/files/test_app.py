import unittest
from app.config import load_config


class TestConfig(unittest.TestCase):
    def test_dev(self):
        c = load_config("dev")
        self.assertEqual(c["db"]["host"], "dev-db")
        self.assertEqual(c["db"]["port"], 5432)
        self.assertEqual(c["db"]["pool"], {"min": 1, "max": 4})
        self.assertTrue(c["debug"])
        self.assertEqual(c["name"], "svc")


if __name__ == "__main__":
    unittest.main()
