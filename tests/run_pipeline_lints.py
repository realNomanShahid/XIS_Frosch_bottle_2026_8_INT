"""Optional ruff lint report for src/ and tests/ (A12 support)."""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "compliance" / "test_reports" / "linter"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    targets = ["src", "tests"]
    cmd = [sys.executable, "-m", "ruff", "check", *targets]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    report = OUT / "A12_ruff_src_tests.txt"
    report.write_text(
        f"generated_at_utc={ts}\nreturncode={proc.returncode}\n\n"
        f"STDOUT\n{proc.stdout}\n\nSTDERR\n{proc.stderr}\n",
        encoding="utf-8",
    )
    print(f"Wrote {report}")
    # ruff may be missing — do not hard-fail the whole repo for that
    if proc.returncode == 1 and "No module named ruff" in (proc.stderr + proc.stdout):
        print("ruff not installed; report still written")
        return 0
    return 0 if proc.returncode in (0, 1) else proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())