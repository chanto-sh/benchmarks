import unittest

from util import slugify


class SlugifyTest(unittest.TestCase):
    def test_spaces(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_underscores(self):
        self.assertEqual(slugify("Already_Slug"), "already-slug")

    def test_padding(self):
        self.assertEqual(slugify("  Padded  "), "padded")


if __name__ == "__main__":
    unittest.main()
