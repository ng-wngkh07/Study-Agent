"""Require a new development-history entry whenever a PR changes project files."""
import argparse
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
HISTORY = "LICH_SU_DU_AN.md"


def entry_ids(content: str) -> list[str]:
    return re.findall(r'^### ((?:YC-\d+)|(?:LOG-[A-Za-z0-9_-]+))\b', content, re.M)


def validate(changed: list[str], current: str, previous: str) -> list[str]:
    errors = []
    ids = entry_ids(current)
    old_ids = entry_ids(previous)
    if not ids or len(ids) != len(set(ids)):
        errors.append("History entries must have unique YC-/LOG- identifiers.")
    if not set(old_ids).issubset(ids):
        errors.append("Do not delete or renumber old shared history entries.")
    substantive = [name for name in changed if name != HISTORY]
    if substantive and (HISTORY not in changed or not (set(ids) - set(old_ids))):
        errors.append("Project changes require a new entry in LICH_SU_DU_AN.md.")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="PR base commit or ref")
    args = parser.parse_args()
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", f"{args.base}...HEAD"], cwd=ROOT,
        text=True, encoding="utf-8").splitlines()
    old = subprocess.run(["git", "show", f"{args.base}:{HISTORY}"], cwd=ROOT,
        capture_output=True, text=True, encoding="utf-8")
    current = (ROOT / HISTORY).read_text(encoding="utf-8")
    errors = validate(changed, current, old.stdout if old.returncode == 0 else "")
    if errors:
        print("\n".join(errors))
        return 1
    print("History check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
