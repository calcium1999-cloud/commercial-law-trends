#!/usr/bin/env python3
"""Restore the pre-redesign presentation while retaining the latest embedded data.

Run without --apply to validate only. This does not publish or alter Git history.
"""
import argparse
import datetime
import json
from pathlib import Path
import re
import subprocess

BACKUP_REF = "backup/pre-editorial-redesign-2026-09-05"
DB_BLOCK = re.compile(r'(<script id="db-data" type="application/json">)(.*?)(</script>)', re.S)


def restore_shell(original, current):
    previous = DB_BLOCK.search(original)
    latest = DB_BLOCK.search(current)
    if len(DB_BLOCK.findall(original)) != 1 or len(DB_BLOCK.findall(current)) != 1:
        raise ValueError("Expected exactly one embedded database in each page")
    json.loads(previous.group(2))
    data = json.loads(latest.group(2))
    result = DB_BLOCK.sub(lambda _: latest.group(0), original)
    assert json.loads(DB_BLOCK.search(result).group(2)) == data
    return result, len(data.get("articles", []))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Back up the current page and restore the previous design locally")
    args = parser.parse_args()
    project = Path(__file__).resolve().parent.parent
    page = project / "index.html"
    original = subprocess.check_output(["git", "show", BACKUP_REF + ":index.html"], cwd=project, text=True)
    current = page.read_text(encoding="utf-8")
    restored, count = restore_shell(original, current)
    print(f"Validated: previous design can be restored while preserving all {count} current articles.")
    if not args.apply:
        print("No files changed. Use --apply to restore locally; publication is a separate step.")
        return
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = project / "backups" / ("before-design-restore-" + stamp + ".html")
    backup.parent.mkdir(exist_ok=True)
    with backup.open("x", encoding="utf-8") as handle:
        handle.write(current)
    page.write_text(restored, encoding="utf-8")
    print(f"Restored locally. Current design saved at {backup}. Nothing published.")


if __name__ == "__main__":
    main()
