"""Write a simple A12-style quality report under compliance/test_reports/."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "compliance" / "test_reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cmd = [sys.executable, "-m", "pytest", "-q", str(ROOT / "tests")]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    payload = {
        "artifact": "A12",
        "project": "Frosch",
        "generated_at_utc": ts,
        "pytest_returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-2000:],
        "note": (
            "Code/evidence contract checks only. Does not claim A09 measurement "
            "validation, signed A02, or production A13 approval."
        ),
    }
    json_path = REPORT_DIR / "A12_code_quality_report.json"
    md_path = REPORT_DIR / "A12_code_quality_report.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(
        "\n".join(
            [
                "# A12 Code Quality Report — Frosch",
                "",
                f"- Generated (UTC): {ts}",
                f"- pytest return code: {proc.returncode}",
                "",
                "## Note",
                payload["note"],
                "",
                "## pytest stdout (tail)",
                "```",
                payload["stdout_tail"],
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())