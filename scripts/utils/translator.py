#!/usr/bin/env python3
"""
translator.py — 中英翻译工具

使用 googletrans 库，内置速率控制和重试。
"""
import logging
import time
from googletrans import Translator as _GT

logger = logging.getLogger(__name__)

_gt = _GT()
_MIN_INTERVAL = 1.5  # 请求间隔（秒）
_last_request_time = 0


def _rate_limit():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_request_time = time.time()


def _translate(text, max_retries=3):
    if not text or not text.strip():
        return ""
    text = text.strip()
    for attempt in range(max_retries):
        try:
            _rate_limit()
            result = _gt.translate(text, dest='zh-cn')
            if result and result.text and result.text != text:
                return result.text
            return ""
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return ""
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
    translated = [r for chunk in chunks if (r := _translate(chunk))]
    return " ".join(translated) if translated else ""


def translate_keywords(keywords):
    if isinstance(keywords, list):
        if not keywords:
            return []
        result = []
        for kw in keywords:
            translated = _translate(str(kw))
            result.append(translated if translated else kw)
        return result
    if isinstance(keywords, str) and keywords.strip():
        return _translate(keywords)
    return ""


def translate_cached(text):
    return _translate(text)


def en_to_zh(text):
    return _translate(text)


def enrich_article_with_cn(article):
    if not article.get('title_cn') and article.get('title'):
        try:
            article['title_cn'] = translate_title(article['title'])
        except Exception:
            pass
    abstract = article.get('abstract', '')
    if not article.get('abstract_cn') and abstract and len(abstract) > 10 and 'not available' not in abstract.lower():
        try:
            article['abstract_cn'] = translate_abstract(abstract)
        except Exception:
            pass
    keywords = article.get('keywords', '')
    if not article.get('keywords_cn') and keywords:
        try:
            article['keywords_cn'] = translate_keywords(keywords)
        except Exception:
            pass
    return article