#!/usr/bin/env python3
"""
translator.py — 中英翻译工具

翻译已改为离线模式：enrich_article_with_cn 不再调用外部 API，
中文字段由 AI 在脚本运行后直接填充。
保留函数签名以兼容调用方。
"""
import logging

logger = logging.getLogger(__name__)


def translate_cached(text):
    return ""


def en_to_zh(text):
    return ""


def translate_title(title):
    return ""


def translate_abstract(abstract):
    return ""


def translate_keywords(keywords):
    if isinstance(keywords, list):
        return []
    return ""


def enrich_article_with_cn(article):
    """
    离线模式：跳过 API 翻译，中文字段留空。
    由 AI 在脚本运行后直接填充 title_cn / abstract_cn / keywords_cn。
    """
    logger.info("翻译已切换为离线模式，跳过 API 调用")
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
