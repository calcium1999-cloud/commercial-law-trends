#!/usr/bin/env python3
"""ECB Banking Supervision Blog — 欧洲央行银行监管博客。

欧洲央行单一监管机制（SSM）官方博客，聚焦银行监管、审慎监管。
"""
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from scrapers.base import BaseScraper, parse_date, fetch_url


class ECBSupervisionScraper(BaseScraper):
    source_id = "ecb_supervision"
    source_name = "ECB Banking Supervision Blog"
    base_url = "https://www.bankingsupervision.europa.eu"
    list_url = "https://www.bankingsupervision.europa.eu/press/blog/html/index.en.html"

    def scrape(self, since_date):
        """从博客列表页抓取。"""
        try:
            html = fetch_url(self.list_url)
            if not html:
                return [], "FAILED", "无法获取列表页"

            articles = self._parse_list(html)
            filtered = [a for a in articles if a.get("date", "") >= since_date]

            # Fetch details for recent ones
            for a in filtered[:10]:
                try:
                    detail = self.fetch_detail(a["url"])
                    a.update(detail)
                except Exception:
                    pass

            return filtered, "SUCCESS", None
        except Exception as e:
            return [], "FAILED", str(e)

    def _parse_list(self, html):
        """Parse blog list page."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        items = []

        # ECB uses .box class with date + title
        boxes = soup.select(".box")
        for box in boxes:
            # Find link to blog post
            links = box.find_all("a", href=True)
            blog_link = None
            for a in links:
                href = a.get("href", "")
                if "/ssm.blog" in href and ".en.html" in href:
                    blog_link = a
                    break

            if not blog_link:
                continue

            url = urljoin(self.base_url, blog_link["href"])
            text = box.get_text(" ", strip=True)

            # Extract date pattern: "6 July 2026"
            date_match = re.search(
                r"(\d{1,2}\s+[A-Z][a-z]+\s+20\d{2})", text
            )
            date_str = date_match.group(1) if date_match else ""
            date = parse_date(date_str) if date_str else None

            # Extract title (text after date)
            title = ""
            if date_str:
                after_date = text.split(date_str, 1)
                if len(after_date) > 1:
                    # Title is usually the next sentence-like chunk
                    title_part = after_date[1].strip()
                    # Take first sentence or up to 150 chars
                    for sep in [". ", "  ", "\n"]:
                        if sep in title_part:
                            title_part = title_part.split(sep, 1)[0]
                            break
                    title = title_part[:150].strip()

            if not title:
                title = blog_link.get_text(strip=True)[:150]

            if title and date:
                items.append({
                    "source_id": self.source_id,
                    "title": title,
                    "title_cn": "",
                    "authors": "ECB Banking Supervision",
                    "affiliations": "European Central Bank",
                    "date": date,
                    "abstract": "",
                    "keywords": "",
                    "url": url,
                    "type": "article",
                })

        return items

    def fetch_detail(self, url):
        """Fetch article detail page for abstract and authors."""
        html = fetch_url(url)
        if not html:
            return {}

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        detail = {}

        # Get main content
        content = soup.find("article") or soup.find("main") or soup.find(class_="content")
        if content:
            paras = content.find_all("p")
            text_paras = [p.get_text(strip=True) for p in paras if len(p.get_text(strip=True)) > 80]
            if text_paras:
                # First 2-3 paras as abstract
                abstract = " ".join(text_paras[:3])
                detail["abstract"] = abstract[:1500]

        # Try to find author
        author_el = soup.find(class_="author") or soup.find(class_="byline")
        if author_el:
            detail["authors"] = author_el.get_text(strip=True)[:200]

        return detail
