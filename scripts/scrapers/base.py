#!/usr/bin/env python3
"""BaseScraper — 所有来源爬虫的公共基类。

使用 curl 作为 HTTP 客户端（macOS LibreSSL 与 requests 不兼容时的稳定方案）。
"""
import re
import time
import subprocess
import hashlib
from datetime import datetime
from urllib.parse import urljoin, urlparse

import feedparser
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
TIMEOUT = 20


def curl_get(url, timeout=TIMEOUT):
    """Use curl subprocess for HTTP GET. Returns text or raises."""
    cmd = [
        "curl", "-s", "-L",
        "--connect-timeout", str(timeout),
        "--max-time", str(timeout * 3),
        "-H", f"User-Agent: {UA}",
        "-H", "Accept: text/html,application/xhtml+xml,application/xml,text/xml,*/*",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout * 4)
    if result.returncode != 0:
        raise ConnectionError(f"curl failed (rc={result.returncode}): {result.stderr[:200]}")
    if not result.stdout:
        raise ConnectionError("curl returned empty response")
    return result.stdout


WAYBACK_PREFIX = "https://web.archive.org/web/2026if_/"


def curl_get_with_fallback(url, timeout=TIMEOUT):
    """Try direct curl_get first; on SSL/connection failure, fall back to Wayback Machine."""
    try:
        return curl_get(url, timeout)
    except (ConnectionError, subprocess.TimeoutExpired) as e:
        wayback_url = f"{WAYBACK_PREFIX}{url}"
        try:
            return curl_get(wayback_url, timeout)
        except Exception:
            raise e


def fetch_url(url):
    """HTTP GET via curl. Returns text or None."""
    try:
        return curl_get(url)
    except Exception:
        return None


def fetch_url_with_fallback(url):
    """HTTP GET via curl with Wayback Machine fallback. Returns text or None."""
    try:
        return curl_get_with_fallback(url)
    except Exception:
        return None


def parse_date(date_str):
    """Parse various date formats, return YYYY-MM-DD string or None."""
    if not date_str:
        return None
    if isinstance(date_str, datetime):
        return date_str.strftime("%Y-%m-%d")
    import time as _time
    if isinstance(date_str, (_time.struct_time, type(_time.localtime()))):
        try:
            return f"{date_str.tm_year:04d}-{date_str.tm_mon:02d}-{date_str.tm_mday:02d}"
        except (AttributeError, ValueError):
            pass
    date_str = str(date_str).strip()
    # Try formats with timezone stripped (LibreSSL %z unreliable)
    stripped = re.sub(r'\s*[+\-]\d{4}\s*$', '', date_str)
    stripped = re.sub(r'\s+UTC\s*$', '', stripped)
    fmts = [
        "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
        "%B %d, %Y", "%b %d, %Y",
        "%d %B %Y", "%d %b %Y",
        "%a, %d %b %Y %H:%M:%S",
        "%A, %d %B %Y", "%a, %d %b %Y",
    ]
    for fmt in fmts:
        for candidate in [stripped, date_str]:
            try:
                dt = datetime.strptime(candidate[:26], fmt)
                return dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                continue
    for m in re.finditer(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str):
        try:
            return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        except ValueError:
            pass
    m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
    if m:
        try:
            return f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
        except ValueError:
            pass
    return None


class BaseScraper:
    source_id = ""
    source_name = ""

    def scrape(self, since_date):
        """Fetch list, filter by date, fetch details. Returns (articles, status, error_msg)."""
        try:
            raw_list = self.fetch_list()
        except Exception as e:
            return [], "FAILED", str(e)

        if not raw_list:
            return [], "SUCCESS", None

        articles = []
        for item in raw_list:
            try:
                pub_date = item.get("date")
                if pub_date and since_date:
                    if pub_date < since_date:
                        continue
                detail = self.fetch_detail(item.get("url", ""))
                if detail:
                    item.update(detail)
                item.setdefault("source_id", self.source_id)
                item.setdefault("type", "article")
                if "abstract" not in item or not item["abstract"]:
                    desc = item.pop("description", "")
                    if desc:
                        item["abstract"] = desc[:500]
                else:
                    item.pop("description", None)
                if "title_cn" not in item:
                    item["title_cn"] = ""
                articles.append(item)
            except Exception:
                continue
        return articles, "SUCCESS", None

    def fetch_list(self):
        raise NotImplementedError

    def fetch_detail(self, url):
        raise NotImplementedError

    @staticmethod
    def _clean(text):
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def _html_to_text(html_str):
        if not html_str:
            return ""
        soup = BeautifulSoup(html_str, "lxml")
        return BaseScraper._clean(soup.get_text(separator=" "))

    @staticmethod
    def _parse_rss(xml_text):
        """Parse RSS/Atom XML with feedparser. Returns list of dicts."""
        feed = feedparser.parse(xml_text)
        items = []
        for entry in feed.entries:
            # Prefer struct_time from feedparser, then string
            date_val = entry.get("published_parsed") or entry.get("updated_parsed")
            if not date_val:
                date_val = entry.get("published", entry.get("updated", ""))
            item = {
                "title": BaseScraper._clean(entry.get("title", "")),
                "url": entry.get("link", ""),
                "date": parse_date(date_val),
                "description": BaseScraper._html_to_text(entry.get("summary", entry.get("description", ""))),
            }
            author = entry.get("author", "")
            if author:
                item["authors"] = author
            items.append(item)
        return items

    @staticmethod
    def _soup(html_text):
        return BeautifulSoup(html_text, "lxml")
