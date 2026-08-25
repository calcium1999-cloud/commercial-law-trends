#!/usr/bin/env python3
"""NY Fed Liberty Street Economics — 纽约联储博客。

高质量的经济学/金融/银行监管研究博客，纽约联储出品。
"""
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from scrapers.base import BaseScraper, parse_date, curl_get


class NYFedScraper(BaseScraper):
    source_id = "nyfed_liberty"
    source_name = "NY Fed Liberty Street Economics"
    rss_url = "https://libertystreeteconomics.newyorkfed.org/feed/"

    def scrape(self, since_date):
        """从 RSS 抓取，过滤 since_date 之后的文章。"""
        try:
            xml = curl_get(self.rss_url)
            items = self._parse_rss(xml)
        except Exception as e:
            return [], "FAILED", str(e)

        # Filter by date
        filtered = []
        for item in items:
            d = item.get("date", "")
            if d and d >= since_date:
                article = self._parse_rss_item(item)
                if article:
                    filtered.append(article)

        return filtered, "SUCCESS", None

    def _parse_rss_item(self, item):
        """Parse RSS item into article dict."""
        title = item.get("title", "").strip()
        if not title:
            return None

        url = item.get("url", "")
        date = item.get("date", "")
        authors = item.get("authors", "")
        description = item.get("description", "")

        # 提取摘要：description 通常是 HTML，取前 500 字
        abstract = description[:600] if description else ""

        # 尝试从 RSS 中提取更多信息
        # Liberty Street 的 RSS 包含 category
        keywords = ""
        if "tags" in item:
            tags = item.get("tags", [])
            if isinstance(tags, list):
                keywords = "; ".join(tags)

        return {
            "source_id": self.source_id,
            "title": title,
            "title_cn": "",
            "authors": authors or "Liberty Street Economics",
            "affiliations": "Federal Reserve Bank of New York",
            "date": date,
            "abstract": abstract,
            "keywords": keywords,
            "url": url,
            "type": "article",
        }
