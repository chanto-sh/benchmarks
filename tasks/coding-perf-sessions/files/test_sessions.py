import unittest

from sessions import bounce_rate, sessionize, top_landing_pages


class SessionsTest(unittest.TestCase):
    def test_basic(self):
        ev = [("bob", 100, "/"), ("ann", 50, "/pricing"), ("bob", 1000, "/docs"), ("bob", 5000, "/"),
              ("ann", 60, "/signup")]
        s = sessionize(ev)
        self.assertEqual([(x["user"], x["start"], x["end"], x["pages"]) for x in s], [
            ("ann", 50, 60, ["/pricing", "/signup"]),
            ("bob", 100, 1000, ["/", "/docs"]),
            ("bob", 5000, 5000, ["/"]),
        ])
        self.assertEqual(top_landing_pages(s), [("/", 2), ("/pricing", 1)])
        self.assertAlmostEqual(bounce_rate(s), 1 / 3)

    def test_custom_gap(self):
        ev = [("u", 0, "a"), ("u", 10, "b"), ("u", 25, "c")]
        self.assertEqual(len(sessionize(ev, gap=10)), 2)

    def test_empty(self):
        self.assertEqual(sessionize([]), [])
        self.assertEqual(top_landing_pages([]), [])
        self.assertEqual(bounce_rate([]), 0.0)


if __name__ == "__main__":
    unittest.main()
