#!/usr/bin/env python3
"""
translator.py — 中英翻译工具

使用 MyMemory Translator（免费 API），用于法律学术文本的翻译。
带速率限制和重试机制。

注意：MyMemory 免费版每天有限额（约 5000 字符/天）。
如需更高额度，可注册 DeepL Free API（每月 50 万字符）后切换。
"""
import time
import logging
from functools import lru_cache

from deep_translator import MyMemoryTranslator

logger = logging.getLogger(__name__)

# 速率限制：每请求间隔（秒）
REQUEST_INTERVAL = 1.0
MAX_RETRIES = 3
RETRY_DELAY = 3

_translator_en_zh = None


def _get_translator():
    """Lazy load translator instance."""
    global _translator_en_zh
    if _translator_en_zh is None:
        _translator_en_zh = MyMemoryTranslator(source='en-US', target='zh-CN')
    return _translator_en_zh


@lru_cache(maxsize=5000)
def translate_cached(text):
    """带缓存的翻译。text 必须是字符串。"""
    return _translate(text)


def _translate(text):
    """核心翻译函数，带重试。"""
    if not text or not text.strip():
        return ""
    
    text = text.strip()
    
    # 极短文本（<2 chars）直接返回
    if len(text) < 2:
        return text
    
    translator = _get_translator()
    
    for attempt in range(MAX_RETRIES):
        try:
            result = translator.translate(text)
            time.sleep(REQUEST_INTERVAL)
            if result and isinstance(result, str) and result.strip():
                return result.strip()
        except Exception as e:
            logger.warning(f"翻译失败（第 {attempt + 1} 次）: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                # 每次重试重新创建 translator 实例
                global _translator_en_zh
                _translator_en_zh = MyMemoryTranslator(source='en-US', target='zh-CN')
            else:
                logger.error(f"翻译最终失败: {text[:80]}...")
                return ""
    
    return ""


def en_to_zh(text):
    """英文翻译成中文。"""
    return translate_cached(text)


def translate_title(title):
    """翻译标题，返回中文标题。"""
    if not title:
        return ""
    return en_to_zh(title)


def translate_abstract(abstract):
    """翻译摘要。长文本分段翻译后拼接。"""
    if not abstract or not abstract.strip():
        return ""
    
    # 如果文本较短（< 400 字符），直接翻译
    if len(abstract) <= 400:
        return en_to_zh(abstract)
    
    # 长文本按句子分割翻译
    sentences = _split_sentences(abstract)
    translated_parts = []
    current_chunk = ""
    
    for sent in sentences:
        if len(current_chunk) + len(sent) < 350:
            current_chunk += sent + " "
        else:
            if current_chunk.strip():
                translated_parts.append(en_to_zh(current_chunk.strip()))
            current_chunk = sent + " "
    
    if current_chunk.strip():
        translated_parts.append(en_to_zh(current_chunk.strip()))
    
    return "".join(translated_parts)


def translate_keywords(keywords):
    """翻译关键词。支持字符串（分号分隔）或列表输入。"""
    if not keywords:
        return [] if isinstance(keywords, list) else ""
    
    # 如果是列表
    if isinstance(keywords, list):
        translated = []
        for kw in keywords:
            if kw and isinstance(kw, str) and kw.strip():
                result = en_to_zh(kw.strip())
                translated.append(result if result else kw)
        return translated
    
    # 如果是字符串
    keywords_str = str(keywords).strip()
    if not keywords_str:
        return ""
    
    kw_list = [k.strip() for k in keywords_str.split(';') if k.strip()]
    translated = []
    for kw in kw_list:
        result = en_to_zh(kw)
        translated.append(result if result else kw)
    
    return "；".join(translated)


def _split_sentences(text):
    """简单的英文句子分割。"""
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def enrich_article_with_cn(article):
    """
    为单篇文章补充中文字段。
    输入 article dict，补充 title_cn, abstract_cn, keywords_cn。
    如果已存在且非空，则跳过。
    """
    # 标题翻译
    if not article.get('title_cn'):
        article['title_cn'] = translate_title(article.get('title', ''))
    
    # 摘要翻译
    if not article.get('abstract_cn') and article.get('abstract'):
        article['abstract_cn'] = translate_abstract(article['abstract'])
    
    # 关键词翻译
    if not article.get('keywords_cn') and article.get('keywords'):
        article['keywords_cn'] = translate_keywords(article['keywords'])

    return article


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)
    
    test_title = "Liability Management's Limited Runway: Corporate Restructuring Today"
    test_abstract = "Coercive, non-pro rata debt restructurings have become a central tool for distressed borrowers over the past decade."
    test_keywords = "Private Equity; Debt; Creditor Rights; Bankruptcy"
    
    print("标题翻译:", translate_title(test_title))
    print("摘要翻译:", translate_abstract(test_abstract))
    print("关键词翻译:", translate_keywords(test_keywords))
