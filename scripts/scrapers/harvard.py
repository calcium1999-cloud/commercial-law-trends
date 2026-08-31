#!/usr/bin/env python3
"""Harvard Law School Forum on Corporate Governance — RSS 爬虫。

SSL 失败时自动回退到 Wayback Machine 缓存。
"""
import re
from .base import BaseScraper, curl_get_with_fallback


class HarvardScraper(BaseScraper):
    source_id = "harvard"
    source_name = "Harvard Law School Forum on Corporate Governance"
    RSS_URL = "https://corpgov.law.harvard.edu/feed/"

    def fetch_list(self):
        text = curl_get_with_fallback(self.RSS_URL)
        items = self._parse_rss_flexible(text)
        result = []
        for item in items:
            if item.get("title") and item.get("url"):
                if "weekly roundup" in item["title"].lower():
                    continue
                result.append(item)
        return result

    def fetch_detail(self, url):
        if not url:
            return {}
        try:
            text = curl_get_with_fallback(url)
            # If response looks like HTML, parse with BeautifulSoup
            if "<html" in text[:500].lower() or "<!doctype" in text[:500].lower():
                return self._parse_html_detail(text)
            # Otherwise it's Jina AI text — parse text format
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
        """Parse Jina AI text format for article details."""
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        detail = {}

        # Find "Posted by" line for authors
        for i, line in enumerate(lines):
            if line.lower().startswith("posted by"):
                # Extract authors from "Posted by X, Y, and Z, on..."
                m = re.match(r"Posted by\s+(.+?),\s+on\s+", line, re.I)
                if m:
                    detail["authors"] = m.group(1).strip()
                break

        # Keywords: line after "E-Mail" in the comment/print/email section
        for i, line in enumerate(lines):
            if line.lower().strip() in ("e-mail", "email"):
                if i + 1 < len(lines):
                    kw_line = lines[i + 1]
                    if "," in kw_line and not kw_line.startswith("http"):
                        kws = [k.strip() for k in kw_line.split(",") if k.strip()]
                        if kws and len(kws) >= 2:
                            detail["keywords"] = kws
                break

        # Abstract: first substantive paragraph after keywords
        content_start = 0
        for i, line in enumerate(lines):
            if "More from:" in line:
                content_start = i + 1
                break
        if content_start > 0:
            paras = []
            for line in lines[content_start:]:
                if len(line) > 50:
                    paras.append(line)
                    if len(paras) >= 2:
                        break
            if paras:
                detail["abstract"] = " ".join(paras)[:1500]

        if not detail.get("abstract"):
            detail.pop("abstract", None)
        return detail
