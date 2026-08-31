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
        text = curl_get_with_fallback(self.RSS_URL)
        items = self._parse_rss_flexible(text)
        result = []
        for item in items:
            if item.get("title") and item.get("url"):
                result.append(item)
        return result

    def fetch_detail(self, url):
        if not url:
            return {}
        try:
            text = curl_get_with_fallback(url)
            if "<html" in text[:500].lower() or "<!doctype" in text[:500].lower():
                return self._parse_html_detail(text)
            return self._parse_text_detail(text)
        except Exception:
            return {}

    def _parse_html_detail(self, html):
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

    def _parse_text_detail(self, text):
        """Parse Jina AI text format for CLS article details."""
        import re
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        detail = {}

        # Find "By [author] [date]" pattern
        for i, line in enumerate(lines):
            m = re.match(r"By\s+(.+?)\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d", line, re.I)
            if m:
                detail["authors"] = m.group(1).strip()
                # Abstract: first long paragraph after this line
                for j in range(i + 1, min(len(lines), i + 20)):
                    if len(lines[j]) > 80 and not lines[j].startswith("http") and "Facebook" not in lines[j] and "Twitter" not in lines[j] and "LinkedIn" not in lines[j]:
                        detail["abstract"] = lines[j][:1500]
                        break
                break

        if not detail.get("abstract"):
            detail.pop("abstract", None)
        return detail
