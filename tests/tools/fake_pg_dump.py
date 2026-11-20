"""Stands in for pg_dump in the tests: writes the arguments it got into the --file, or fails on request."""

import os
import sys

if os.environ.get("FAKE_PG_DUMP_FAIL"):
    sys.stderr.write("pg_dump: error: connection refused\n")
    sys.exit(1)
out = next(a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--file="))
with open(out, "w", encoding="utf-8") as f:
    f.write(" ".join(sys.argv[1:]) + "\nPGPASSWORD=" + os.environ.get("PGPASSWORD", ""))
