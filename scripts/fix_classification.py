#!/usr/bin/env python3
"""修复数据库中缺少 primary_topic 的文章分类，并更新本期按语。"""
import json
import sys
from pathlib import Path

PROJECT = Path("/Users/endofmay/Documents/博士/商法研究趋势")
DB_PATH = PROJECT / "database" / "articles.json"
sys.path.insert(0, str(PROJECT / "scripts"))

from utils.classifier import classify

with DB_PATH.open(encoding="utf-8") as f:
    db = json.load(f)

fixed = 0
for art in db.get("articles", []):
    if not art.get("primary_topic"):
        title = art.get("title", "")
        abstract = art.get("abstract", "")
        keywords = art.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(",")]
        topics, primary = classify(title, abstract, keywords)
        art["topics"] = topics
        art["primary_topic"] = primary
        fixed += 1
        print(f"  fixed: [{art.get('id', '?')}] {title[:60]} → {primary}")

print(f"\n共修复 {fixed} 篇文章的分类")

# Also fix the latest report trends
from utils.report_gen import SOURCE_NAMES, TOPIC_NAMES, TOPIC_ORDER
from collections import Counter

latest_report_id = "2026-08-27"
report = next((r for r in db.get("reports", []) if r["id"] == latest_report_id), None)
if report:
    # Get articles for this report
    report_articles = [a for a in db["articles"] if a.get("report_id") == latest_report_id]
    if report_articles:
        trends = []
        total = len(report_articles)
        topic_dist = Counter(a.get("primary_topic", "other") for a in report_articles)
        source_dist = Counter(a.get("source_id", "") for a in report_articles)
        active_sources = "、".join(SOURCE_NAMES.get(s, s) for s in source_dist if source_dist[s] > 0)
        topic_str = "、".join(f"{TOPIC_NAMES.get(t, t)}（{c}篇）" for t, c in topic_dist.most_common(3))
        trends.append(f"本周十一大来源共新增{total}篇文章，来自{active_sources}，主题分布以{topic_str}为主。")
        for topic_id in TOPIC_ORDER:
            topic_arts = [a for a in report_articles if topic_id in (a.get("topics") or [])]
            if topic_arts:
                topic_name = TOPIC_NAMES[topic_id]
                sources_in_topic = set(a.get("source_id") for a in topic_arts)
                source_str = "、".join(SOURCE_NAMES.get(s, s) for s in sources_in_topic)
                titles = [a.get("title_cn") or a.get("title", "") for a in topic_arts]
                titles_short = [t[:50] for t in titles[:3]]
                trends.append(
                    f"{topic_name}领域新增{len(topic_arts)}篇，来自{source_str}。"
                    f"本期重点议题包括{'；'.join(titles_short)}{'等' if len(titles) > 3 else ''}。"
                )
        report["trends"] = trends
        report["summary"] = f"本周十一大来源共新增{total}篇文章。"
        print(f"\n已更新报告 {latest_report_id} 的本期按语:")
        for t in trends:
            print(f"  {t}")

with DB_PATH.open("w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=2)

print(f"\n数据库已保存")
