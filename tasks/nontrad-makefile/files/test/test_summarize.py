import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import summarize  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"


class SummarizeTests(unittest.TestCase):
    def test_totals(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            summarize.main([str(FIX / "one.csv")])
        got = json.loads(buf.getvalue())
        self.assertEqual(got["skus"]["X1"], {"units": 3, "revenue": "3.30"})


if __name__ == "__main__":
    unittest.main()
