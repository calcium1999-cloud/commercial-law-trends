#!/usr/bin/env python3
"""周报 Markdown 生成器 — 按照既有周报格式生成。"""
import sys
import os
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent

SOURCE_ORDER = ["ecgi", "harvard", "oblb", "promarket", "cls", "yale", "jotwell", "banking_with_interest", "nyfed_liberty", "ecb_supervision", "bank_underground"]
SOURCE_NAMES = {
    "ecgi": "ECGI",
    "harvard": "Harvard",
    "oblb": "OBLB",
    "promarket": "ProMarket",
    "cls": "CLS",
    "yale": "Yale JREG",
    "jotwell": "Jotwell",
    "banking_with_interest": "BWI",
    "nyfed_liberty": "NY Fed",
    "ecb_supervision": "ECB",
    "bank_underground": "BoE",
}
TOPIC_NAMES = {
    "corporate_governance": "公司治理",
    "financial_regulation": "金融监管",
    "antitrust": "反垄断",
    "tech_data_ai": "科技、数据与AI",
    "other": "其他",
}
TOPIC_ORDER = ["corporate_governance", "financial_regulation", "antitrust", "tech_data_ai", "other"]


def generate_report(report_id, period_start, period_end, articles, source_status, gen_time=None):
    """Generate weekly report Markdown string."""
    if gen_time is None:
        gen_time = datetime.now()

    lines = []
    lines.append("# 商业法律研究动向\n")
    lines.append(f"**报告周期**：{period_start} — {period_end}")
    lines.append(f"**数据来源**：ECGI | Harvard | OBLB | ProMarket | CLS | Yale JREG | Jotwell | BWI | NY Fed | ECB | BoE\n")

    # Group articles by source
    by_source = defaultdict(list)
    for art in articles:
        by_source[art.get("source_id", "")].append(art)

    total = len(articles)

    # Trends section
    lines.append("## 📊 本周研究趋势概括\n")
    topic_dist = Counter(a.get("primary_topic", "other") for a in articles)
    source_dist = Counter(a.get("source_id", "") for a in articles)

    trends = []
    if total == 0:
        trends.append("本周十一大来源均无新增文章，可能是各机构发布周期所致。")
    else:
        # Overview paragraph
        active_sources = [s for s in source_dist if source_dist[s] > 0]
        active_source_names = "、".join(SOURCE_NAMES.get(s, s) for s in active_sources)
        top_topics = topic_dist.most_common(3)
        topic_str = "、".join(f"{TOPIC_NAMES.get(t, t)}（{c}篇）" for t, c in top_topics)
        trends.append(f"本周十一大来源共新增{total}篇文章，来自{active_source_names}，主题分布以{topic_str}为主。")

        # Analytical paragraph per topic
        for topic_id in TOPIC_ORDER:
            topic_arts = [a for a in articles if topic_id in (a.get("topics") or [])]
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

        failed_sources = [s for s, st in source_status.items() if st == "FAILED"]
        if failed_sources:
            failed_names = "、".join(SOURCE_NAMES.get(s, s) for s in failed_sources)
            trends.append(f"本周{failed_names}来源无法访问，未完成抓取。")

    for t in trends:
        lines.append(t)
    lines.append("")

    # Articles by source
    lines.append("## 📄 各来源新文章\n")
    for sid in SOURCE_ORDER:
        sname = SOURCE_NAMES.get(sid, sid)
        status = source_status.get(sid, "UNKNOWN")
        arts = by_source.get(sid, [])

        if status == "FAILED":
            lines.append(f"### {sname}")
            lines.append("> 本周无法访问，未完成抓取。\n")
        elif not arts:
            lines.append(f"### {sname}")
            lines.append("> 本周无新文章。\n")
        else:
            lines.append(f"### {sname}（{len(arts)} 篇）\n")
            for art in arts:
                lines.append(f"#### {art.get('title', 'N/A')}")
                lines.append(f"**作者**：{art.get('authors', 'Not stated')}")
                lines.append(f"**Affiliations**：{art.get('affiliations', 'Not stated')}")
                abstract = art.get("abstract", "")
                if abstract:
                    lines.append(f"**摘要**：{abstract}")
                else:
                    lines.append("**摘要**：Not available")
                keywords = art.get("keywords", [])
                if isinstance(keywords, list):
                    kw_str = "; ".join(keywords)
                else:
                    kw_str = str(keywords)
                lines.append(f"**关键词**：{kw_str}")
                topics = art.get("topics", [])
                topic_names = [TOPIC_NAMES.get(t, t) for t in topics]
                lines.append(f"**主题**：{', '.join(topic_names)}")
                lines.append(f"**原文链接**：{art.get('url', 'N/A')}\n")

    # Index by topic
    lines.append("## 📌 索引\n")
    for topic_id in TOPIC_ORDER:
        topic_name = TOPIC_NAMES[topic_id]
        topic_arts = [a for a in articles if topic_id in (a.get("topics") or [])]
        lines.append(f"### {topic_name}")
        if topic_arts:
            for art in topic_arts:
                sname = SOURCE_NAMES.get(art.get("source_id", ""), "")
                title_display = art.get("title_cn") or art.get("title", "N/A")
                lines.append(f"- [{sname}] {title_display} — {art.get('url', '')}")
        else:
            lines.append("（本周无相关文章）")
        lines.append("")

    # Footer
    lines.append(f"\n---\n*生成时间：{gen_time.strftime('%Y-%m-%d %H:%M:%S')}*\n")

    return "\n".join(lines)


def generate_report_metadata(report_id, period_start, period_end, articles, trends):
    """Generate report metadata dict for temp_report.json."""
    total = len(articles)
    summary = f"本周十一大来源共新增{total}篇文章。"
    return {
        "id": report_id,
        "date": report_id,
        "period_start": period_start,
        "period_end": period_end,
        "title": "商业法律研究动向",
        "summary": summary,
        "trends": trends,
    }


if __name__ == "__main__":
    print("Report generator module. Use via run_weekly.py.")
