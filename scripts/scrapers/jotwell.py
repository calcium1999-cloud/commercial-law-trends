#!/usr/bin/env python3
"""Jotwell Corporate Law — RSS 爬虫。"""
from .base import BaseScraper, curl_get


class JotwellScraper(BaseScraper):
    source_id = "jotwell"
    source_name = "Jotwell - Corporate Law"
    RSS_URL = "https://corp.jotwell.com/feed/"

    def fetch_list(self):
        xml = curl_get(self.RSS_URL)
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
