#!/usr/bin/env python3
"""Banking with Interest (IntraFi / Rob Blackwell) 播客爬虫。

RSS-based podcast scraper.
"""
import sys
import re
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scrapers.base import BaseScraper, parse_date, curl_get
from bs4 import BeautifulSoup

RSS_URL = "https://bankingwithinterest.libsyn.com/rss"
SOURCE_ID = "banking_with_interest"
SOURCE_NAME = "Banking with Interest"

logger = logging.getLogger(__name__)


class BankingWithInterestScraper(BaseScraper):
    source_id = SOURCE_ID
    source_name = SOURCE_NAME

    def scrape(self, since_date=None):
        """Fetch RSS and parse podcast episodes."""
        try:
            xml_text = curl_get(RSS_URL)
        except Exception as e:
            return [], "FAILED", str(e)

        try:
            feed = self._parse_rss(xml_text)
        except Exception as e:
            return [], "FAILED", f"RSS parse error: {e}"

        articles = []
        for item in feed:
            # Date check
            date_str = item.get("date", "")
            if since_date and date_str and date_str < since_date:
                continue

            title = item.get("title", "")
            if not title:
                continue

            # Build article dict
            article = {
                "source_id": SOURCE_ID,
                "title": title,
                "title_cn": "",
                "authors": "Rob Blackwell",
                "affiliations": "IntraFi",
                "date": date_str or "",
                "abstract": item.get("description", "")[:2000],
                "abstract_cn": "",
                "keywords": "Banking Policy; Financial Regulation; Bank Supervision",
                "keywords_cn": "",
                "topics": ["financial_regulation"],
                "primary_topic": "financial_regulation",
                "url": item.get("url", ""),
                "type": "podcast",
                "duration": "",
                "guests": "",
            }
            articles.append(article)

        return articles, "SUCCESS", ""


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = BankingWithInterestScraper()
    articles, status, err = scraper.scrape("2026-01-01")
    print(f"Status: {status}")
    if err:
        print(f"Error: {err}")
    print(f"Articles: {len(articles)}")
    for a in articles[:3]:
        print(f"  - {a['date']} | {a['title'][:80]}")
