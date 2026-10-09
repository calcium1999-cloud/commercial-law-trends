#!/usr/bin/env python3
"""Bank Underground — 英格兰银行官方博客。

聚焦货币政策、银行监管、金融稳定，BoE 研究人员撰写。
"""
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from scrapers.base import BaseScraper, parse_date, curl_get


class BankUndergroundScraper(BaseScraper):
    source_id = "bank_underground"
    source_name = "Bank Underground (Bank of England)"
    rss_url = "https://bankunderground.co.uk/feed/atom/"

    def scrape(self, since_date):
        """从 Atom RSS 抓取。"""
        try:
            xml = curl_get(self.rss_url)
            items = self._parse_rss(xml)
        except Exception as e:
            return [], "FAILED", str(e)

        filtered = []
        for item in items:
            d = item.get("date", "")
            if d and d >= since_date:
                article = self._parse_item(item)
                if article:
                    filtered.append(article)

        return filtered, "SUCCESS", None

    def _parse_item(self, item):
        """Parse RSS item into article dict."""
        title = item.get("title", "").strip()
        if not title:
            return None

        url = item.get("url", "")
        date = item.get("date", "")
        authors = item.get("authors", "")
        description = item.get("description", "")

        # The Atom feed often exposes only the generic site account as author,
        # while the real byline is the first bold paragraph in the article.
        if not authors or authors.replace(" ", "").lower() in {"bankunderground", "bankofengland"}:
            authors = self._fetch_byline(url) or authors

        if authors and description.startswith(authors):
            description = description[len(authors):].lstrip(" :-–—")
        description = re.sub(r"\s*Continue reading\b.*$", "", description, flags=re.I).strip()

        # Atom feeds sometimes have content
        abstract = description[:600] if description else ""

        return {
            "source_id": self.source_id,
            "title": title,
            "title_cn": "",
            "authors": authors or "Bank Underground",
            "affiliations": "Bank of England",
            "date": date,
            "abstract": abstract,
            "keywords": "",
            "url": url,
            "type": "article",
        }

    def _fetch_byline(self, url):
        """Recover the substantive article byline from the first bold paragraph."""
        if not url:
            return ""
        try:
            soup = self._soup(curl_get(url))
            byline = soup.select_one(".entry-content p strong, article p strong, main p strong")
            if byline:
                text = self._clean(byline.get_text(" ", strip=True))
                if 2 <= len(text.split()) <= 12:
                    return text
        except Exception:
            pass
        return ""
