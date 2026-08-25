#!/usr/bin/env python3
"""fix_database.py — 修复数据库中 37 篇 primary_topic 为 null 的文章。"""
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "database" / "articles.json"
HTML_PATH = PROJECT_DIR / "index.html"
sys.path.insert(0, str(PROJECT_DIR / "scripts"))

from utils.classifier import classify
from utils.url_normalize import normalize_url
import re

VALID_TOPICS = {"corporate_governance", "financial_regulation", "antitrust", "tech_data_ai", "other"}


def fix_null_primary_topic(db):
    fixed = 0
    for art in db.get("articles", []):
        if not art.get("primary_topic"):
            title = art.get("title", "")
            abstract = art.get("abstract", "")
            keywords = art.get("keywords", [])
            if isinstance(keywords, str):
                keywords = [k.strip() for k in re.split(r"[,，]", keywords) if k.strip()]
            topics, primary = classify(title, abstract, keywords)
            if not art.get("topics"):
                art["topics"] = topics
            elif isinstance(art["topics"], list):
                if primary in art["topics"]:
                    art["primary_topic"] = primary
                else:
                    art["primary_topic"] = art["topics"][0]
            else:
                art["primary_topic"] = primary
            fixed += 1
    return fixed


def fix_types(db):
    fixed = 0
    for art in db.get("articles", []):
        if isinstance(art.get("authors"), list):
            art["authors"] = ", ".join(str(x) for x in art["authors"])
            fixed += 1
        if isinstance(art.get("affiliations"), list):
            art["affiliations"] = "; ".join(str(x) for x in art["affiliations"])
            fixed += 1
        if isinstance(art.get("keywords"), str):
            art["keywords"] = [k.strip() for k in re.split(r"[,，]", art["keywords"]) if k.strip()]
        if isinstance(art.get("topics"), str):
            art["topics"] = [art["topics"]]
    return fixed


def fix_invalid_topics(db):
    fixed = 0
    for art in db.get("articles", []):
        topics = art.get("topics", [])
        if isinstance(topics, list):
            valid = [t for t in topics if t in VALID_TOPICS]
            if len(valid) != len(topics):
                art["topics"] = valid if valid else ["other"]
                fixed += 1
            primary = art.get("primary_topic")
            if primary and primary not in art["topics"]:
                art["primary_topic"] = art["topics"][0] if art["topics"] else "other"
                fixed += 1
            if not art.get("primary_topic") and art["topics"]:
                art["primary_topic"] = art["topics"][0]
                fixed += 1
    return fixed


def update_html(db):
    html = HTML_PATH.read_text(encoding="utf-8")
    pretty = json.dumps(db, ensure_ascii=False, indent=2)
    new_block = '<script id="db-data" type="application/json">\n' + pretty + '\n</script>'
    pattern = re.compile(r'<script id="db-data" type="application/json">.*?</script>', re.DOTALL)
    new_html, n = pattern.subn(new_block, html, count=1)
    if n == 1:
        HTML_PATH.write_text(new_html, encoding="utf-8")
        print(f"已同步更新: {HTML_PATH}")
    else:
        print(f"警告: 未在 index.html 中找到 db-data 块")


def main():
    print(f"加载数据库: {DB_PATH}")
    with DB_PATH.open(encoding="utf-8") as f:
        db = json.load(f)

    total = len(db.get("articles", []))
    null_count = sum(1 for a in db["articles"] if not a.get("primary_topic"))
    print(f"  总文章数: {total}")
    print(f"  primary_topic 为 null: {null_count}")

    fixed1 = fix_null_primary_topic(db)
    print(f"  修复 null primary_topic: {fixed1} 篇")

    fixed2 = fix_types(db)
    print(f"  修复类型问题: {fixed2} 处")

    fixed3 = fix_invalid_topics(db)
    print(f"  修复非法 topics: {fixed3} 处")

    null_remaining = sum(1 for a in db["articles"] if not a.get("primary_topic"))
    print(f"  剩余 null primary_topic: {null_remaining}")

    # Save
    DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已保存: {DB_PATH}")
    update_html(db)
    print(f"完成。文章总数: {len(db['articles'])}")


if __name__ == "__main__":
    main()
