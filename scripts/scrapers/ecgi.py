#!/usr/bin/env python3
"""ECGI — Working Papers + Blog HTML 爬虫。"""
import re
from urllib.parse import urljoin
from .base import BaseScraper, curl_get, parse_date


class ECGIScraper(BaseScraper):
    source_id = "ecgi"
    source_name = "European Corporate Governance Institute"
    WP_URL = "https://www.ecgi.global/publications/working-papers"
    BLOG_URL = "https://www.ecgi.global/publications/ecgi-blog"
    BASE = "https://www.ecgi.global"

    def fetch_list(self):
        items = []
        for url, art_type in [(self.WP_URL, "working_paper"), (self.BLOG_URL, "blog")]:
            try:
                html = curl_get(url)
                soup = self._soup(html)
                rows = soup.find_all("li", class_="views-row")
                for row in rows:
                    card = row.find("article")
                    if not card:
                        continue
                    link = card.find("a", href=True)
                    if not link:
                        continue
                    href = link.get("href", "")
                    if not href.startswith("http"):
                        href = urljoin(self.BASE, href)
                    if "/working-papers/" not in href and "/blog/" not in href:
                        continue
                    if href.endswith("/faq") or href.endswith("/about") or "editorial-board" in href:
                        continue
                    title_el = card.find("h3") or card.find("h2") or card.find(class_=lambda x: x and "title" in str(x).lower() if x else False)
                    title = title_el.get_text(strip=True) if title_el else link.get_text(strip=True)
                    date_el = card.find("time") or card.find(class_=lambda x: x and "date" in str(x).lower() if x else False)
                    date_str = date_el.get("datetime") or date_el.get_text(strip=True) if date_el else ""
                    items.append({
                        "title": self._clean(title),
                        "url": href,
                        "date": parse_date(date_str),
                        "type": art_type,
                    })
            except Exception:
                continue
        return items

    def fetch_detail(self, url):
        if not url:
            return {}
        try:
            html = curl_get(url)
            soup = self._soup(html)
            detail = {}
            author_els = soup.find_all(class_=lambda x: x and "author" in str(x).lower() if x else False)
            if author_els:
                author_text = author_els[-1].get_text(strip=True)
                author_text = re.sub(r'^Authors?\s*', '', author_text)
                detail["authors"] = self._clean(author_text)
            desc = soup.find("meta", attrs={"name": "description"})
            if desc and desc.get("content"):
                detail["abstract"] = self._clean(desc["content"])
            if not detail.get("abstract"):
                content = soup.find("div", class_="field--name-body") or \
                          soup.find("div", class_="node__content") or \
                          soup.find("article")
                if content:
                    paras = content.find_all("p")
                    text = " ".join(p.get_text(strip=True) for p in paras[:5] if p.get_text(strip=True))
                    if text:
                        detail["abstract"] = text[:1500]
            # Fallback: h2 "Abstract" → next <p> (ECGI new layout)
            if not detail.get("abstract"):
                h2_abstract = soup.find("h2", string="Abstract")
                if h2_abstract:
                    next_p = h2_abstract.find_next("p")
                    if next_p:
                        text = next_p.get_text(strip=True)
                        if text and len(text) > 30:
                            detail["abstract"] = text[:1500]
            tags = soup.find_all("a", href=re.compile(r"/taxonomy/term"))
            if tags:
                detail["keywords"] = list(dict.fromkeys(t.get_text(strip=True) for t in tags if t.get_text(strip=True)))
            if not detail.get("abstract"):
                detail.pop("abstract", None)
            return detail
        except Exception:
            return {}

    def fetch_detail_with_fallback(self, url):
        """Try HTML parsing first; fall back to Jina AI text if no abstract found."""
        detail = self.fetch_detail(url)
        if detail.get("abstract"):
            return detail
        # Jina AI fallback
        try:
            from .base import jina_get
            text = jina_get(url, timeout=30)
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            paras = []
            for line in lines:
                if len(line) > 100 and not line.startswith("http") and "cookie" not in line.lower() and "gdpr" not in line.lower():
                    paras.append(line)
                    if len(paras) >= 2:
                        break
            if paras:
                detail["abstract"] = " ".join(paras)[:1500]
            if not detail.get("authors"):
                for i, line in enumerate(lines):
                    if "author" in line.lower() and i + 1 < len(lines):
                        detail["authors"] = lines[i + 1].strip()
                        break
        except Exception:
            pass
        if not detail.get("abstract"):
            detail.pop("abstract", None)
        return detail
