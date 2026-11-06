#!/usr/bin/env python3
"""CLS Blue Sky (Columbia Law School Blogs) — RSS 爬虫。

SSL 失败时自动回退到 Wayback Machine 缓存。
"""
import re

from .base import BaseScraper, curl_get_with_fallback


class CLSScraper(BaseScraper):
    source_id = "cls"
    source_name = "Columbia Law School Blogs - CLS Blue Sky"
    RSS_URL = "https://clsbluesky.law.columbia.edu/feed/"

    def fetch_list(self):
        text = curl_get_with_fallback(self.RSS_URL)
        items = self._parse_rss_flexible(text)
        # WordPress exposes internal posting accounts in dc:creator.  Prefer
        # the substantive attribution paragraph at the end of each post.
        try:
            import feedparser
            feed = feedparser.parse(text)
            attributed = {}
            for entry in feed.entries:
                content = (entry.get("content") or [{}])[0].get("value", "")
                soup = self._soup(content)
                paras = soup.find_all("p")
                attribution_text = paras[-1].get_text(" ", strip=True) if paras else self._html_to_text(content)
                authors = self._extract_attribution(attribution_text)
                if entry.get("link") and authors:
                    attributed[entry["link"]] = authors
            for item in items:
                if item.get("url") in attributed:
                    item["authors"] = attributed[item["url"]]
        except Exception:
            pass
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
        entry = soup.find("div", class_="entry-content") or soup.find("article")
        if not detail.get("abstract"):
            if entry:
                paras = entry.find_all("p")
                text = " ".join(p.get_text(strip=True) for p in paras[:3] if p.get_text(strip=True))
                if text:
                    detail["abstract"] = text[:1500]
        if entry:
            paras = entry.find_all("p")
            attribution_text = paras[-1].get_text(" ", strip=True) if paras else entry.get_text(" ", strip=True)
            authors = self._extract_attribution(attribution_text)
            if authors:
                detail["authors"] = authors
        if entry and not detail.get("authors"):
            # Scope the visible byline to the current post.  A global
            # ``.author`` lookup can select the unrelated feature-bar cards
            # rendered before the article (for example John C. Coffee on a
            # Brett McDonnell post).
            post = entry.find_parent(id=re.compile(r"^post-")) or entry.find_parent("article")
            if post:
                names = []
                for author_el in post.select(".entry-meta a[rel='author']"):
                    name = self._clean(author_el.get_text(" ", strip=True))
                    if name and name.casefold() not in {"renholding"} and name not in names:
                        names.append(name)
                if names:
                    detail["authors"] = ", ".join(names)
        if not detail.get("authors"):
            author_el = soup.select_one("div[id^='post-'] .entry-meta a[rel='author']")
            if author_el:
                detail["authors"] = self._clean(author_el.get_text(" ", strip=True))
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

        # A substantive closing credit (for example a law-firm memorandum,
        # official remarks, or a Shadow SEC statement) should override the
        # visible WordPress byline.  Generic biography matches, however, must
        # not override it: Jina output can end with unrelated sidebar bios.
        tail = " ".join(lines[-80:])
        explicit_credit = re.search(
            r"(?:These remarks were delivered|This statement was issued|"
            r"This post comes to us from the Shadow SEC|"
            r"This post is based on an?\s+.+?\s+memorandum)",
            tail,
            re.I,
        )
        authors = self._extract_attribution(tail)
        if authors and (explicit_credit or not detail.get("authors")):
            detail["authors"] = authors

        if not detail.get("abstract"):
            detail.pop("abstract", None)
        return detail

    @staticmethod
    def _extract_attribution(text):
        """Extract the credited author(s) from CLS's closing attribution."""
        if not text:
            return ""
        tail = " ".join(text.split())[-4000:]
        m = re.search(
            r"These remarks were delivered.*?\bby\s+(.+?),\s+(?:chair|commissioner|director|professor)\b",
            tail,
            re.I,
        )
        if m:
            return m.group(1).strip()
        m = re.search(
            r"This statement was issued.*?\bby\s+(.+?),\s+chief accountant,\s+and\s+(.+?),\s+director\b",
            tail,
            re.I,
        )
        if m:
            return f"{m.group(1).strip()}, {m.group(2).strip()}"
        m = re.search(
            r"This post comes to us from the Shadow SEC, whose members are professors\s+(.+?)(?:\.\s+ENDNOTES|$)",
            tail,
            re.I,
        )
        if m:
            names = re.findall(
                r"([A-Z][A-Za-z.\-']+(?:\s+[A-Z][A-Za-z.\-']+){1,3}(?:,\s+Jr\.)?)\s+at\s+",
                m.group(1),
            )
            if names:
                return ", ".join(name.strip() for name in names)
        m = re.search(r"This post is based on an? (.+? LLP) memorandum", tail, re.I)
        if m:
            credited = m.group(1).strip()
            if credited.casefold() == "davis, polk & wardwell llp":
                credited = "Davis Polk & Wardwell LLP"
            elif credited.casefold() == "laham & watkins llp":
                # The 2026-11-05 CLS post misspells the firm's name in its
                # closing credit; the post title correctly identifies Latham.
                credited = "Latham & Watkins LLP"
            return credited
        # Some law firms are credited without an ``LLP`` suffix (for example,
        # "Wachtell, Lipton, Rosen & Katz memorandum").  Keep this after the
        # narrower LLP form and anchor it to CLS's standard closing sentence so
        # sidebar authors cannot leak into the attribution.
        m = re.search(
            r"This post is based on an?\s+(.+?)\s+memorandum(?:,|\b)",
            tail,
            re.I,
        )
        if m:
            credited = m.group(1).strip()
            if credited.casefold() == "davis, polk & wardwell llp":
                credited = "Davis Polk & Wardwell LLP"
            elif credited.casefold() == "laham & watkins llp":
                credited = "Latham & Watkins LLP"
            return credited
        names = re.findall(
            r"([A-Z][A-Za-zÀ-ÖØ-öø-ÿ\-’']*"
            r"(?:\s+(?:[A-Z][A-Za-zÀ-ÖØ-öø-ÿ\-’']*|[A-Z]\.)){1,6}"
            r"(?:,\s+Jr\.)?)\s+is\s+(?:a|an|the)\b",
            tail,
        )
        cleaned = []
        for name in names:
            name = name.strip()
            if name and name not in cleaned:
                cleaned.append(name)
        return ", ".join(cleaned)
