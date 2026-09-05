#!/usr/bin/env python3
"""
update_db.py — 增量更新 articles.json 和 index.html

用法:
    python3 update_db.py <new_articles.json>
    python3 update_db.py <new_articles.json> --dry-run

职责:
  1. 读 database/articles.json（已存在的文章库）
  2. 读入新文章 JSON
  3. 按 URL 去重（同 URL 文章不重复入库）
  4. 校验每篇新文章的 topics 是否在 5 主题分类内
  5. 分配新 id (art_NNN)，追加到 articles 列表
  6. 写回 database/articles.json
  7. 替换 index.html 中 <script id="db-data" type="application/json">...</script> 的内容

新文章 JSON 格式（数组，每篇为一个对象）:
[
  {
    "report_id": "2026-07-24",
    "source_id": "ecgi",         // 必须是 sources 列表中已有的 id
    "title": "...",
    "title_cn": "...",
    "authors": "...",
    "affiliations": "...",
    "date": "2026-07-22",
    "abstract": "...",
    "keywords": ["...", "..."],
    "topics": ["corporate_governance"],   // 5 主题 id 之一，可多选
    "primary_topic": "corporate_governance",  // topics 中的第一个
    "url": "https://...",
    "type": "working_paper"  // 或 "blog" 等
  },
  ...
]
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "database" / "articles.json"
HTML_PATH = PROJECT_DIR / "index.html"

# 5 主题白名单（与 index.html 和 articles.json 中的 topics 数组保持一致）
VALID_TOPICS = {
    "corporate_governance",
    "financial_regulation",
    "antitrust",
    "tech_data_ai",
    "other",
}


def load_db():
    with DB_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def load_new_articles(path: Path):
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(
            f"新文章文件必须是 JSON 数组，但得到了 {type(data).__name__}"
        )
    return data


def normalize_article(art: dict):
    """字段类型归一化：authors/affiliations/keywords/topics 统一类型。

    前端 index.html 按字符串处理 authors/affiliations，按数组处理 keywords/topics，
    若直接写入错误类型会导致渲染 JS 抛 TypeError、文章列表整体空白。
    """
    if isinstance(art.get("authors"), list):
        art["authors"] = ", ".join(str(x) for x in art["authors"])
    if isinstance(art.get("affiliations"), list):
        art["affiliations"] = "; ".join(str(x) for x in art["affiliations"])
    # keywords: string -> list (split by comma or Chinese comma)
    if isinstance(art.get("keywords"), str):
        art["keywords"] = [kw.strip() for kw in re.split(r"[,，]\s*", art["keywords"]) if kw.strip()]
    # topics: string -> list
    if isinstance(art.get("topics"), str):
        art["topics"] = [art["topics"]]
    return art


def validate_article(art: dict, source_ids: set, report_ids: set, idx: int):
    """Return a list of error strings (empty = valid)."""
    errors = []
    required = ["source_id", "title", "abstract", "url"]
    for field in required:
        if not art.get(field):
            errors.append(f"#{idx}: 缺少必填字段 {field!r}")
    # date 允许为空，自动填充 report_id 日期
    if not art.get("date"):
        art["date"] = art.get("report_id", datetime.now().strftime("%Y-%m-%d"))

    if art.get("source_id") and art["source_id"] not in source_ids:
        errors.append(
            f"#{idx}: source_id={art['source_id']!r} 不在已知来源中 "
            f"(已知: {sorted(source_ids)})"
        )

    for f_name in ("authors", "affiliations"):
        if f_name in art and not isinstance(art[f_name], (str, list)):
            errors.append(
                f"#{idx}: {f_name} 必须是字符串或数组，"
                f"但得到了 {type(art[f_name]).__name__}"
            )

    if art.get("report_id") and art["report_id"] not in report_ids:
        # 警告而非错误 — 新报告 id 是允许的（毕竟这就是新增报告）
        pass

    topics = art.get("topics", [])
    if not topics:
        errors.append(f"#{idx}: 缺少 topics 字段（应至少包含 1 个主题）")
    else:
        for t in topics:
            if t not in VALID_TOPICS:
                errors.append(
                    f"#{idx}: topic={t!r} 不在 5 主题白名单中 "
                    f"(合法: {sorted(VALID_TOPICS)})"
                )

    primary = art.get("primary_topic")
    if primary and primary not in VALID_TOPICS:
        errors.append(f"#{idx}: primary_topic={primary!r} 不在白名单中")
    if primary and primary not in topics:
        errors.append(
            f"#{idx}: primary_topic={primary!r} 不在 topics 列表 {topics} 中"
        )

    return errors


def assign_ids(db, new_articles):
    """给新文章分配递增的 id (art_NNN)。"""
    existing_ids = [int(a["id"].split("_")[1]) for a in db["articles"]
                    if a["id"].startswith("art_") and a["id"][4:].isdigit()]
    next_n = max(existing_ids) + 1 if existing_ids else 1
    for art in new_articles:
        if not art.get("id"):
            art["id"] = f"art_{next_n:03d}"
            next_n += 1
    return new_articles


def normalize_url(url):
    """URL 规范化：去 fragment、去 tracking 参数、统一 HTTPS、去尾部斜杠。"""
    from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
    p = urlparse(url)
    scheme = "https"
    netloc = p.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = p.path.rstrip("/")
    tracking_prefixes = ("utm_", "fbclid", "gclid", "ref", "source")
    query = urlencode(
        sorted((k, v) for k, v in parse_qsl(p.query)
               if not any(k.lower().startswith(t) for t in tracking_prefixes))
    )
    return urlunparse((scheme, netloc, path, "", query, "")) if query else \
           urlunparse((scheme, netloc, path, "", "", ""))


def dedupe(db, new_articles):
    """按规范化 URL 去重 — 已存在 URL 的文章跳过。"""
    existing_urls = {normalize_url(a["url"]) for a in db["articles"]}
    existing_raw = {a["url"] for a in db["articles"]}
    added, skipped = [], []
    for art in new_articles:
        norm = normalize_url(art["url"])
        if norm in existing_urls or art["url"] in existing_raw:
            skipped.append(art)
        else:
            added.append(art)
            existing_urls.add(norm)
            existing_raw.add(art["url"])
    return added, skipped


def update_meta(db):
    """更新 meta.last_updated 字段。"""
    db["meta"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")


def update_html(db):
    """替换 index.html 中 <script id="db-data" type="application/json">...</script> 的内容。"""
    html = HTML_PATH.read_text(encoding="utf-8")
    pretty = json.dumps(db, ensure_ascii=False, indent=2)
    new_block = (
        '<script id="db-data" type="application/json">\n'
        + pretty
        + '\n</script>'
    )
    pattern = re.compile(
        r'<script id="db-data" type="application/json">.*?</script>',
        re.DOTALL,
    )
    # Use a callable replacement so JSON backslashes (for example ``\\n`` in
    # scraped abstracts) are not interpreted as regex replacement escapes.
    new_html, n = pattern.subn(lambda _match: new_block, html, count=1)
    if n != 1:
        raise RuntimeError(
            f"未在 index.html 中找到 <script id=\"db-data\"> 块（实际匹配 {n} 次）"
        )
    HTML_PATH.write_text(new_html, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="增量更新 articles.json 和 index.html")
    ap.add_argument("new_file", type=Path, help="新文章 JSON 文件路径")
    ap.add_argument("--dry-run", action="store_true",
                    help="只校验，不实际写入")
    args = ap.parse_args()

    if not args.new_file.exists():
        print(f"ERROR: 文件不存在: {args.new_file}", file=sys.stderr)
        sys.exit(1)

    print(f"加载数据库: {DB_PATH}")
    db = load_db()
    source_ids = {s["id"] for s in db["sources"]}
    report_ids = {r["id"] for r in db["reports"]}
    print(f"  已存在 {len(db['articles'])} 篇文章, "
          f"{len(source_ids)} 个来源, {len(report_ids)} 个报告")

    print(f"加载新文章: {args.new_file}")
    new_articles = load_new_articles(args.new_file)
    print(f"  待入库 {len(new_articles)} 篇")

    # 归一化 + 校验
    new_articles = [normalize_article(a) for a in new_articles]
    all_errors = []
    for i, art in enumerate(new_articles):
        all_errors.extend(validate_article(art, source_ids, report_ids, i))

    if all_errors:
        print("\n校验失败:")
        for err in all_errors:
            print(f"  - {err}")
        sys.exit(1)
    print("  校验通过")

    # 去重
    added, skipped = dedupe(db, new_articles)
    print(f"  新增: {len(added)} 篇, 跳过(URL重复): {len(skipped)} 篇")
    if skipped:
        for s in skipped:
            print(f"    skip: {s['url']}")

    # 分配 id
    added = assign_ids(db, added)
    for a in added:
        print(f"    add: [{a['id']}] {a.get('title_cn') or a['title'][:50]}")

    if args.dry_run:
        print("\n[DRY RUN] 不写入任何文件。")
        return

    # 写入数据库
    db["articles"].extend(added)
    update_meta(db)

    # 自动关联 article_ids 到对应 report
    report_map = {}
    for r in db["reports"]:
        rid = r["id"]
        report_map[rid] = r
    for art in added:
        rid = art.get("report_id")
        if rid and rid in report_map:
            r = report_map[rid]
            if "article_ids" not in r:
                r["article_ids"] = []
            if art["id"] not in r["article_ids"]:
                r["article_ids"].append(art["id"])

    DB_PATH.write_text(
        json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n已更新: {DB_PATH}")

    # 写入 HTML
    update_html(db)
    print(f"已更新: {HTML_PATH}")

    print(f"\n完成。文章总数: {len(db['articles'])}")


if __name__ == "__main__":
    main()
