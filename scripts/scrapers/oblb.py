#!/usr/bin/env python3
"""OBLB — Oxford Business Law Blog HTML 爬虫。"""
import re
from urllib.parse import urljoin
from .base import BaseScraper, curl_get, parse_date


class OBLBScraper(BaseScraper):
    source_id = "oblb"
    source_name = "Oxford Business Law Blog"
    MAIN_URL = "https://blogs.law.ox.ac.uk/"
    BASE = "https://blogs.law.ox.ac.uk"

    def fetch_list(self):
        html = curl_get(self.MAIN_URL)
        soup = self._soup(html)
        items = []
        for a in soup.find_all("a", href=re.compile(r"/oblb/blog-post/")):
            href = a.get("href", "")
            if not href.startswith("http"):
                href = urljoin(self.BASE, href)
            text = a.get_text(strip=True)
            if not text or len(text) < 10:
                continue
            date_m = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', text)
            date_str = date_m.group(1) if date_m else ""
            title = re.sub(r'^\d{1,2}\s+\w+\s+\d{4}', '', text).strip()
            title = re.sub(r'^by:.*$', '', title).strip()
            if not title:
                continue
            items.append({
                "title": self._clean(title),
                "url": href,
                "date": parse_date(date_str),
                "type": "blog",
            })
        seen = set()
        deduped = []
        for item in items:
            if item["url"] not in seen:
                seen.add(item["url"])
                deduped.append(item)
        return deduped

    def fetch_detail(self, url):
        if not url:
            return {}
        try:
            html = curl_get(url)
            soup = self._soup(html)
            detail = {}
            desc = soup.find("meta", attrs={"name": "description"})
            if desc and desc.get("content"):
                detail["abstract"] = self._clean(desc["content"])
            if not detail.get("abstract"):
                content = soup.find("div", class_="field--name-body") or soup.find("article") or soup.find("div", class_="content")
                if content:
                    paras = content.find_all("p")
                    text = " ".join(p.get_text(strip=True) for p in paras[:3] if p.get_text(strip=True))
                    if text:
                        detail["abstract"] = text[:1500]
            author_el = soup.find(class_=lambda x: x and "author" in str(x).lower() if x else False)
            if author_el:
                author_text = re.sub(r'^by:\s*', '', author_el.get_text(strip=True), flags=re.I)
                detail["authors"] = self._clean(author_text)
            tags = soup.find_all("a", href=re.compile(r"/oblb/tag/|/taxonomy/term/"))
            if tags:
                detail["keywords"] = list(dict.fromkeys(t.get_text(strip=True) for t in tags if t.get_text(strip=True)))
            if not detail.get("abstract"):
                detail.pop("abstract", None)
            return detail
        except Exception:
            return {}
