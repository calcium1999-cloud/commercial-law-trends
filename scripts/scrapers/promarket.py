#!/usr/bin/env python3
"""ProMarket (Stigler Center) — RSS 爬虫，过滤非商法文章。"""
import re
from .base import BaseScraper, curl_get

NON_COMMERCIAL_PATTERNS = [
    r'abortion', r'birth control', r'smartphone ban', r'slaveholder',
    r'newspaper competition.*rebellion', r'call for.*application',
    r'liberal democracy', r'global imbalance', r'g7 is failing',
    r'social institution', r'property rights.*exit',
]


def is_commercial_law(title, description):
    text = (title + " " + description).lower()
    for pat in NON_COMMERCIAL_PATTERNS:
        if re.search(pat, text):
            return False
    return True


class ProMarketScraper(BaseScraper):
    source_id = "promarket"
    source_name = "ProMarket / Stigler Center"
    RSS_URL = "https://www.promarket.org/feed/"

    def fetch_list(self):
        xml = curl_get(self.RSS_URL)
        items = self._parse_rss(xml)
        result = []
        for item in items:
            if not item.get("title") or not item.get("url"):
                continue
            desc = item.get("description", "")
            if not is_commercial_law(item["title"], desc):
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
            tags = soup.find_all("a", rel="tag") or soup.find_all("a", class_="tag")
            if tags:
                detail["keywords"] = [t.get_text(strip=True) for t in tags if t.get_text(strip=True)]
            if not detail.get("abstract"):
                detail.pop("abstract", None)
            return detail
        except Exception:
            return {}
