#!/usr/bin/env python3
"""
translate_articles.py — 批量翻译文章的摘要和关键词

用法:
    python translate_articles.py [--limit N] [--all]

默认翻译最新的 10 篇没有中文摘要的文章。
"""
import json
import sys
import logging
import argparse
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "database" / "articles.json"

sys.path.insert(0, str(PROJECT_DIR / "scripts"))
from utils.translator import translate_abstract, translate_keywords, translate_title

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="翻译文章摘要和关键词")
    parser.add_argument("--limit", type=int, default=10, help="翻译数量（默认10）")
    parser.add_argument("--all", action="store_true", help="翻译所有缺少中文摘要的文章")
    args = parser.parse_args()

    with open(DB_PATH, 'r', encoding='utf-8') as f:
        db = json.load(f)

    articles = db['articles']
    
    # 找出需要翻译的文章（按日期倒序）
    to_translate = [
        a for a in sorted(articles, key=lambda x: x.get('date', ''), reverse=True)
        if not a.get('abstract_cn') and a.get('abstract')
    ]

    if not args.all:
        to_translate = to_translate[:args.limit]

    if not to_translate:
        print("没有需要翻译的文章")
        return

    print(f"共 {len(to_translate)} 篇文章需要翻译")
    print(f"预计需要约 {len(to_translate) * 2} 秒（标题+摘要+关键词）\n")

    success = 0
    fail = 0

    for i, article in enumerate(to_translate, 1):
        print(f"[{i}/{len(to_translate)}] {article['date']} | {article['title'][:60]}")

        try:
            # 翻译标题（如果没有）
            if not article.get('title_cn'):
                article['title_cn'] = translate_title(article.get('title', ''))
                if article['title_cn']:
                    print(f"  标题: {article['title_cn'][:50]}")

            # 翻译摘要
            abstract = article.get('abstract', '')
            if abstract and not article.get('abstract_cn'):
                # 跳过非常短的摘要
                if len(abstract) > 10 and 'not available' not in abstract.lower():
                    article['abstract_cn'] = translate_abstract(abstract)
                    if article['abstract_cn']:
                        print(f"  摘要: {article['abstract_cn'][:50]}...")
                        success += 1
                    else:
                        print(f"  摘要: 翻译失败")
                        fail += 1
                else:
                    article['abstract_cn'] = ''
                    print(f"  摘要: 跳过（无有效内容）")

            # 翻译关键词
            keywords = article.get('keywords', '')
            if keywords and not article.get('keywords_cn'):
                article['keywords_cn'] = translate_keywords(keywords)
                if article['keywords_cn']:
                    print(f"  关键词: {article['keywords_cn'][:50]}")

        except Exception as e:
            print(f"  错误: {e}")
            fail += 1

        # 每翻译 5 篇保存一次
        if i % 5 == 0:
            with open(DB_PATH, 'w', encoding='utf-8') as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
            print(f"  (已保存)\n")

    # 最终保存
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"\n完成！成功 {success} 篇，失败 {fail} 篇")
    print(f"数据库已保存到 {DB_PATH}")


if __name__ == "__main__":
    main()
