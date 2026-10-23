import unittest

from textkit import title_case, wrap


class CoreTest(unittest.TestCase):
    def test_title_case(self):
        self.assertEqual(title_case("hello wORLD"), "Hello World")

    def test_wrap(self):
        self.assertEqual(wrap("a bb ccc dddd", 6), ["a bb", "ccc", "dddd"])


if __name__ == "__main__":
    unittest.main()
