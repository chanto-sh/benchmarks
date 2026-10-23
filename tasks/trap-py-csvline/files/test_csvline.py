import unittest

from csvline import split_csv_line


class SplitCsvLine(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(split_csv_line("a,b,c"), ["a", "b", "c"])

    def test_empty_fields(self):
        self.assertEqual(split_csv_line("a,,c,"), ["a", "", "c", ""])

    def test_quoted_comma(self):
        self.assertEqual(split_csv_line('x,"hello, world",y'), ["x", "hello, world", "y"])

    def test_escaped_quote(self):
        self.assertEqual(split_csv_line('"say ""hi""",2'), ['say "hi"', "2"])

    def test_empty_quoted(self):
        self.assertEqual(split_csv_line('"",x'), ["", "x"])


if __name__ == "__main__":
    unittest.main()
