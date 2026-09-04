#!/usr/bin/env python3
"""ECGI — Working Papers + Blog HTML 爬虫。支持分页和降级抓取。"""
import re
from urllib.parse import urljoin
from .base import BaseScraper, curl_get, parse_date


class ECGIScraper(BaseScraper):
    source_id = "ecgi"
    source_name = "European Corporate Governance Institute"
    WP_URL = "https://www.ecgi.global/publications/working-papers"
    BLOG_URL = "https://www.ecgi.global/publications/ecgi-blog"
    BASE = "https://www.ecgi.global"

    def _parse_listing_items(self, html, art_type):
        """从列表页面 HTML 中提取文章条目。"""
        soup = self._soup(html)
        items = []
        # 优先用 .view__results 容器内的 li.views-row
        container = soup.select_one(".view__results")
        scope = container if container else soup
        rows = scope.find_all("li", class_="views-row")
        if not rows:
            # 降级：直接找 article.card
            rows = soup.find_all("article", class_=lambda c: c and "card" in c)
            for card in rows:
                item = self._parse_card(card, art_type)
                if item:
                    items.append(item)
            return items
        for row in rows:
            card = row.find("article")
            if not card:
                continue
            item = self._parse_card(card, art_type)
            if item:
                items.append(item)
        return items

    def _parse_card(self, card, art_type):
        """从 article.card 元素中提取标题、链接、日期。"""
        link = card.find("a", href=True)
        if not link:
            return None
        href = link.get("href", "")
        if not href.startswith("http"):
            href = urljoin(self.BASE, href)
        if "/working-papers/" not in href and "/blog/" not in href:
            return None
        if href.endswith("/faq") or href.endswith("/about") or "editorial-board" in href:
            return None
        # 标题
        title_el = card.find(class_="card__title") or card.find("h2") or card.find("h3")
        title = title_el.get_text(strip=True) if title_el else link.get_text(strip=True)
        # 日期
        time_el = card.find("time")
        date_str = time_el.get("datetime") or time_el.get_text(strip=True) if time_el else ""
        return {
            "title": self._clean(title),
            "url": href,
            "date": parse_date(date_str),
            "type": art_type,
        }

    def _get_next_page_url(self, html, current_url):
        """获取下一页 URL，无则返回 None。"""
        soup = self._soup(html)
        next_link = soup.select_one(".pager__item--next a")
        if next_link and next_link.get("href"):
            return urljoin(self.BASE, next_link["href"])
        return None

    def fetch_list(self, max_pages=3):
        """抓取列表页，最多翻 max_pages 页。"""
        items = []
        seen_urls = set()
        for url, art_type in [(self.WP_URL, "working_paper"), (self.BLOG_URL, "blog")]:
            page_url = url
            for page in range(max_pages):
                try:
                    html = curl_get(page_url)
                except Exception:
                    break
                page_items = self._parse_listing_items(html, art_type)
                new_count = 0
                for item in page_items:
                    if item["url"] not in seen_urls:
                        seen_urls.add(item["url"])
                        items.append(item)
                        new_count += 1
                if new_count == 0:
                    break
                page_url = self._get_next_page_url(html, page_url)
                if not page_url:
                    break
        return items

    def fetch_detail(self, url):
        if not url:
            return {}
        try:
            html = curl_get(url)
            soup = self._soup(html)
            detail = {}
            # 作者
            author_els = soup.find_all(class_=lambda x: x and "author" in str(x).lower() if x else False)
            if author_els:
                author_text = author_els[-1].get_text(strip=True)
                author_text = re.sub(r'^Authors?\s*', '', author_text)
                detail["authors"] = self._clean(author_text)
            # 摘要
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
            if not detail.get("abstract"):
                h2_abstract = soup.find("h2", string="Abstract")
                if h2_abstract:
                    next_p = h2_abstract.find_next("p")
                    if next_p:
                        text = next_p.get_text(strip=True)
                        if text and len(text) > 30:
                            detail["abstract"] = text[:1500]
            # 关键词
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