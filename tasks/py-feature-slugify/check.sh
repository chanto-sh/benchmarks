#!/bin/bash
cat > /tmp/_hidden_slug_test.py <<'PY'
import sys, unittest
sys.path.insert(0, ".")
from text_utils import slugify
class T(unittest.TestCase):
    def test_all(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")
        self.assertEqual(slugify("  Crème Brûlée  "), "creme-brulee")
        self.assertEqual(slugify("a--b__c"), "a-b-c")
        self.assertEqual(slugify("The quick brown fox", max_length=13), "the-quick")
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("Año Nuevo 2024"), "ano-nuevo-2024")
        self.assertEqual(slugify("über cool", max_length=4), "uber")
        self.assertEqual(slugify("abc", max_length=10), "abc")
        self.assertEqual(slugify("-x-"), "x")
unittest.main(argv=["x"])
PY
python3 /tmp/_hidden_slug_test.py 2>&1 && ls test_text_utils.py >/dev/null 2>&1 && python3 -m unittest -q test_text_utils 2>&1
