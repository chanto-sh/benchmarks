import subprocess, sys, unittest


def run(*a):
    return subprocess.run([sys.executable, "-m", "todo", *a], capture_output=True, text=True)


class CliTest(unittest.TestCase):
    def test_list(self):
        r = run("list")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(len(r.stdout.splitlines()), 5)

    def test_unknown(self):
        r = run("nope")
        self.assertEqual((r.returncode, r.stderr.strip()), (2, "error: unknown command"))


if __name__ == "__main__":
    unittest.main()
