#!/usr/bin/env python3
"""CLS Blue Sky (Columbia Law School Blogs) — RSS 爬虫。

SSL 失败时自动回退到 Wayback Machine 缓存。
"""
from .base import BaseScraper, curl_get_with_fallback


class CLSScraper(BaseScraper):
    source_id = "cls"
    source_name = "Columbia Law School Blogs - CLS Blue Sky"
    RSS_URL = "https://clsbluesky.law.columbia.edu/feed/"

    def fetch_list(self):
        xml = curl_get_with_fallback(self.RSS_URL)
        items = self._parse_rss(xml)
        result = []
        for item in items:
            if item.get("title") and item.get("url"):
                result.append(item)
        return result

    def fetch_detail(self, url):
        if not url:
            return {}
        try:
            html = curl_get_with_fallback(url)
            soup = self._soup(html)
            detail = {}
            desc = soup.find("meta", attrs={"name": "description"})
            if desc and desc.get("content"):
                detail["abstract"] = self._clean(desc["content"])
            if not detail.get("abstract"):
                entry = soup.find("div", class_="entry-content") or soup.find("article")
                if entry:
                    paras = entry.find_all("p")
                    text = " ".join(p.get_text(strip=True) for p in paras[:3] if p.get_text(strip=True))
                    if text:
                        detail["abstract"] = text[:1500]
            author_el = soup.find(class_=lambda x: x and "author" in str(x).lower() if x else False)
            if author_el:
                detail["authors"] = self._clean(author_el.get_text(strip=True))
            tags = soup.find_all("a", rel="tag")
            if tags:
                detail["keywords"] = [t.get_text(strip=True) for t in tags if t.get_text(strip=True)]
            if not detail.get("abstract"):
                detail.pop("abstract", None)
            return detail
        except Exception:
            return {}
