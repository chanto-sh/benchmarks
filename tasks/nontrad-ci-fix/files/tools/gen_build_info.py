"""Write the build-info module the app imports at startup."""
import os
import sys

out = sys.argv[1]
commit = os.environ.get("GIT_COMMIT", "local")
with open(out, "w") as f:
    f.write(f"COMMIT = {commit!r}\nBUILD = 'ci'\n")
print(f"wrote {out}")
