#!/usr/bin/env python3
"""
translator.py — 中英翻译工具

使用 requests 直接调用 Google Translate API（免费端点）。
"""
import logging
import time
import json
import urllib.request
import urllib.parse

logger = logging.getLogger(__name__)

# Google Translate 免费 API 端点
_API_URL = "https://translate.googleapis.com/translate_a/single"


def _translate(text, max_retries=3):
    """翻译单段文本，英译中。"""
    if not text or not text.strip():
        return ""
    text = text.strip()
    for attempt in range(max_retries):
        try:
            params = {
                "client": "gtx",
                "sl": "en",
                "tl": "zh-CN",
                "dt": "t",
                "q": text
            }
            url = _API_URL + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            # Extract translated text from response
            parts = []
            for segment in data[0]:
                if segment[0]:
                    parts.append(segment[0])
            result = "".join(parts)
            if result and result != text:
                return result
            time.sleep(0.5)
            return ""
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                logger.warning(f"翻译失败（{max_retries}次重试）: {str(e)[:80]}")
                return ""


def translate_title(title):
    if not title:
        return ""
    return _translate(title)


def translate_abstract(abstract):
    if not abstract:
        return ""
    if len(abstract) <= 1000:
        return _translate(abstract)
    sentences = abstract.replace('. ', '.|').replace('.\n', '.|').split('|')
    chunks = []
    current = ""
    for s in sentences:
        if len(current) + len(s) < 800:
            current += s + ". "
        else:
            if current:
                chunks.append(current.strip())
            current = s + ". "
    if current:
        chunks.append(current.strip())
    if not chunks:
        return _translate(abstract)
    translated = []
    for chunk in chunks:
        result = _translate(chunk)
        if result:
            translated.append(result)
        time.sleep(0.3)
    return " ".join(translated) if translated else ""


def translate_keywords(keywords):
    if isinstance(keywords, list):
        if not keywords:
            return []
        result = []
        for kw in keywords:
            translated = _translate(str(kw))
            result.append(translated if translated else kw)
            time.sleep(0.2)
        return result
    if isinstance(keywords, str) and keywords.strip():
        return _translate(keywords)
    return ""


def translate_cached(text):
    return _translate(text)


def en_to_zh(text):
    return _translate(text)


def enrich_article_with_cn(article):
    """为文章填充中文翻译字段。"""
    if not article.get('title_cn') and article.get('title'):
        try:
            article['title_cn'] = translate_title(article['title'])
            logger.info(f"  标题翻译: {article['title_cn'][:50] if article['title_cn'] else '失败'}")
        except Exception as e:
            logger.warning(f"  标题翻译异常: {e}")

    abstract = article.get('abstract', '')
    if not article.get('abstract_cn') and abstract and len(abstract) > 10 and 'not available' not in abstract.lower():
        try:
            article['abstract_cn'] = translate_abstract(abstract)
            logger.info(f"  摘要翻译: {article['abstract_cn'][:50] if article['abstract_cn'] else '失败'}...")
        except Exception as e:
            logger.warning(f"  摘要翻译异常: {e}")

    keywords = article.get('keywords', '')
    if not article.get('keywords_cn') and keywords:
        try:
            article['keywords_cn'] = translate_keywords(keywords)
            logger.info(f"  关键词翻译: {str(article['keywords_cn'])[:50]}")
        except Exception as e:
            logger.warning(f"  关键词翻译异常: {e}")

    return article


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("标题:", translate_title("How does the Mandatory Bid Rule Reshape Corporate Acquisition Deals?"))
    print("摘要:", translate_abstract("The mandatory bid rule requires an acquirer to offer to purchase remaining shares."))
    print("关键词:", translate_keywords(["M&A", "Takeovers", "Private Equity"]))