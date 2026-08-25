#!/usr/bin/env python3
"""Yale Journal on Regulation — RSS 爬虫，过滤行政性内容。"""
import re
from .base import BaseScraper, curl_get

SKIP_PATTERNS = [
    r'call for papers', r'call for.*submission',
    r'd\.c\. circuit review', r'dc circuit review',
    r'casebook supplement', r'special issue',
    r'new scholarship corner', r'reading room',
]


def is_substantive(title, description):
    text = (title + " " + description).lower()
    for pat in SKIP_PATTERNS:
        if re.search(pat, text):
            return False
    return True


class YaleScraper(BaseScraper):
    source_id = "yale"
    source_name = "Yale Journal on Regulation"
    RSS_URL = "https://www.yalejreg.com/feed/"

    def fetch_list(self):
        xml = curl_get(self.RSS_URL)
        items = self._parse_rss(xml)
        result = []
        for item in items:
            if not item.get("title") or not item.get("url"):
                continue
            desc = item.get("description", "")
            if not is_substantive(item["title"], desc):
                continue
            result.append(item)
        return result

    def fetch_detail(self, url):
        if not url:
            return {}
        try:
            html = curl_get(url)
            soup = self._soup(html)
            detail = {}
            desc = soup.find("meta", attrs={"name": "description"})
            if desc:
                detail["abstract"] = self._clean(desc.get("content", ""))
            if not detail.get("abstract"):
                entry = soup.find("div", class_="entry-content") or soup.find("article")
                if entry:
                    paras = entry.find_all("p")
                    text = " ".join(p.get_text(strip=True) for p in paras[:3])
                    detail["abstract"] = text[:1000] if text else ""
            tags = soup.find_all("a", rel="tag")
            if tags:
                detail["keywords"] = [t.get_text(strip=True) for t in tags if t.get_text(strip=True)]
            if not detail.get("abstract"):
                detail.pop("abstract", None)
            return detail
        except Exception:
            return {}
