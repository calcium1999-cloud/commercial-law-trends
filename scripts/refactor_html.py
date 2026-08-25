#!/usr/bin/env python3
"""
Refactor index.html: move `const DB = {...}` into a `<script type="application/json">` block.

This eliminates the entire class of "Chinese nested quotes" escaping bugs that plagued
the previous version. JSON inside a <script type="application/json"> is treated as raw
text and parsed by JSON.parse() in a separate script tag.
"""
import json
import re
import sys
from pathlib import Path

HTML_PATH = Path("/Users/endofmay/Documents/博士/商法研究趋势/index.html")


def main():
    html = HTML_PATH.read_text(encoding="utf-8")

    # 1. Locate the `const DB = {...};` assignment.
    #    It is currently a single line: `const DB = {...JSON...};`
    m = re.search(r"^(const DB = )(\{.*?\})(;)\s*$", html, re.MULTILINE | re.DOTALL)
    if not m:
        # Already refactored? Check for the new structure.
        if 'id="db-data"' in html and 'type="application/json"' in html:
            print("Already refactored — no change needed.")
            return
        print("ERROR: could not find `const DB = {...};` line.", file=sys.stderr)
        sys.exit(1)

    db_json_str = m.group(2)
    print(f"Found const DB. Length: {len(db_json_str):,} chars")

    # 2. Validate the JSON parses (this is the old format — may need fixes).
    try:
        db = json.loads(db_json_str)
    except json.JSONDecodeError as e:
        print(f"ERROR: DB is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    n_articles = len(db.get("articles", []))
    print(f"Loaded {n_articles} articles. Pretty-printing...")

    # 3. Pretty-print the JSON for human readability inside the script tag.
    pretty = json.dumps(db, ensure_ascii=False, indent=2)

    # 4. Build the new block.
    new_block = (
        '<script id="db-data" type="application/json">\n'
        + pretty
        + '\n'
        + '</script>\n\n'
        + '<script>\n'
        + '// ===== Database (loaded from <script type="application/json">) =====\n'
        + 'const DB = JSON.parse(document.getElementById("db-data").textContent);\n'
    )

    # 5. Replace the old `const DB = ...;` line.
    new_html = html[:m.start()] + new_block + html[m.end():]

    HTML_PATH.write_text(new_html, encoding="utf-8")
    print(f"Refactored. New file size: {len(new_html):,} chars")
    print(f"Articles preserved: {n_articles}")


if __name__ == "__main__":
    main()
