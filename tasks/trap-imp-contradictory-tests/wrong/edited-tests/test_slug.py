import unittest

from slug import slugify


class SlugTests(unittest.TestCase):
    def test_lowercase_and_spaces(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_strips_punctuation(self):
        self.assertEqual(slugify("What's new, in 2.0?"), "whats-new-in-20")

    def test_collapses_dashes(self):
        self.assertEqual(slugify("a -- b"), "a-b")

    def test_accents(self):
        self.assertEqual(slugify("Crème Brûlée"), "creme-brulee")

    def test_trims(self):
        self.assertEqual(slugify("  --Hi--  "), "hi")

    def test_preserves_underscores(self):
        # Spec 4.2: identifiers keep their underscores.
        self.assertEqual(slugify("user_id field"), "user_id-field")


if __name__ == "__main__":
    unittest.main()
