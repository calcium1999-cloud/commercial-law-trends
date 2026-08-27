#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply translations from translations.json to articles.json"""
import json
from pathlib import Path

DB_PATH = Path("/Users/endofmay/Documents/博士/商法研究趋势/database/articles.json")
TRANS_PATH = Path("/Users/endofmay/Documents/博士/商法研究趋势/database/translations.json")

with DB_PATH.open(encoding="utf-8") as f:
    db = json.load(f)

with TRANS_PATH.open(encoding="utf-8") as f:
    translations = json.load(f)

count = 0
for article in db["articles"]:
    aid = article.get("id", "")
    if aid in translations:
        trans = translations[aid]
        if trans.get("title_cn"):
            article["title_cn"] = trans["title_cn"]
        if trans.get("abstract_cn"):
            article["abstract_cn"] = trans["abstract_cn"]
        count += 1

with DB_PATH.open("w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=2)

print("Translated %d articles" % count)
print("Database saved")

# Clean up
TRANS_PATH.unlink()
