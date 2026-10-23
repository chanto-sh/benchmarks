import re, sys, unittest

from textkit import slugify


class Slug(unittest.TestCase):
    def test_cases(self):
        for given, want in [("  Hello, World! ", "hello-world"), ("A--b__c", "a-b-c"),
                            ("Ünïcode café 9", "n-code-caf-9"), ("---", ""), ("x", "x")]:
            self.assertEqual(slugify(given), want, given)


class Changelog(unittest.TestCase):
    def test_unreleased_entry(self):
        text = open("CHANGELOG.md").read()
        m = re.search(r"^## Unreleased\n(.*?)(?=^## )", text, re.S | re.M)
        self.assertTrue(m, "no Unreleased section")
        self.assertRegex(m.group(1).lower(), r"^- .*slugify", "AGENTS.md: changes go under ## Unreleased")
        released = text[m.end():]
        self.assertNotIn("slugify", released.lower(), "released sections must not change")


if __name__ == "__main__":
    unittest.main()
