#!/usr/bin/env python3
"""
run_weekly.py — 商业法律研究动向 周自动化主协调器

工作流:
  1. 记录 start_time
  2. 读取 state.json（增量窗口）
  3. 抓取 11 个来源（单来源失败不影响其他）
  4. 增量判断（last_successful_run → now）
  5. 去重（规范化 URL）
  6. 主题分类
  7. 中英翻译（标题、摘要、关键词）
  8. 生成周报 Markdown
  9. 生成 temp_report.json + temp_new_articles.json
  10. 调用 add_report.py + update_db.py
  11. 验证数据库
  12. 更新 state.json
  13. 部署到 GitHub Pages
  14. 清理临时文件
"""
import json
import sys
import os
import re
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Setup paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"
DB_PATH = PROJECT_DIR / "database" / "articles.json"
STATE_PATH = PROJECT_DIR / "database" / "state.json"
LOGS_DIR = PROJECT_DIR / "logs"
REPORTS_DIR = PROJECT_DIR / "周报"
TEMP_REPORT_PATH = PROJECT_DIR / "database" / "temp_report.json"
TEMP_ARTICLES_PATH = PROJECT_DIR / "database" / "temp_new_articles.json"

sys.path.insert(0, str(SCRIPTS_DIR))

from scrapers.ecgi import ECGIScraper
from scrapers.harvard import HarvardScraper
from scrapers.oblb import OBLBScraper
from scrapers.promarket import ProMarketScraper
from scrapers.cls import CLSScraper
from scrapers.yale import YaleScraper
from scrapers.jotwell import JotwellScraper
from scrapers.banking_with_interest import BankingWithInterestScraper
from scrapers.nyfed import NYFedScraper
from scrapers.ecb_supervision import ECBSupervisionScraper
from scrapers.bank_underground import BankUndergroundScraper
from utils.classifier import classify
from utils.report_gen import generate_report, generate_report_metadata, SOURCE_NAMES, TOPIC_NAMES, TOPIC_ORDER
from utils.url_normalize import normalize_url

SOURCE_ORDER = ["ecgi", "harvard", "oblb", "promarket", "cls", "yale", "jotwell", "banking_with_interest", "nyfed_liberty", "ecb_supervision", "bank_underground"]
SCRAPERS = {
    "ecgi": ECGIScraper,
    "harvard": HarvardScraper,
    "oblb": OBLBScraper,
    "promarket": ProMarketScraper,
    "cls": CLSScraper,
    "yale": YaleScraper,
    "jotwell": JotwellScraper,
    "banking_with_interest": BankingWithInterestScraper,
    "nyfed_liberty": NYFedScraper,
    "ecb_supervision": ECBSupervisionScraper,
    "bank_underground": BankUndergroundScraper,
}


def setup_logging():
    LOGS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = LOGS_DIR / f"run_{ts}.log"
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return log_file


def load_state():
    if STATE_PATH.exists():
        with STATE_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    STATE_PATH.parent.mkdir(exist_ok=True)
    with STATE_PATH.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def load_db():
    with DB_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def get_since_date(state, db):
    """Determine the incremental window start date."""
    last_run = state.get("last_successful_run")
    if last_run:
        return last_run[:10]
    dates = sorted([a.get("date", "") for a in db.get("articles", []) if a.get("date")])
    if dates:
        return dates[-1]
    return "2026-01-01"


def get_existing_urls(db):
    """Get set of normalized existing URLs for dedup."""
    existing = set()
    for a in db.get("articles", []):
        existing.add(normalize_url(a.get("url", "")))
        existing.add(a.get("url", ""))
    return existing


def run_scrapers(since_date):
    """Run all 11 scrapers. Returns (all_articles, source_status)."""
    all_articles = []
    source_status = {}
    for sid in SOURCE_ORDER:
        scraper_cls = SCRAPERS.get(sid)
        if not scraper_cls:
            source_status[sid] = "FAILED"
            continue
        scraper = scraper_cls()
        logging.info(f"抓取 {sid}...")
        try:
            articles, status, err = scraper.scrape(since_date)
            if status == "FAILED":
                source_status[sid] = "FAILED"
                logging.error(f"  {sid} 抓取失败: {err}")
            else:
                source_status[sid] = "SUCCESS"
                logging.info(f"  {sid} 抓取成功: {len(articles)} 篇 (窗口 {since_date} 之后)")
            all_articles.extend(articles)
        except Exception as e:
            source_status[sid] = "FAILED"
            logging.error(f"  {sid} 异常: {e}")
    return all_articles, source_status


def filter_and_dedup(articles, existing_urls):
    """Filter out articles already in DB by normalized URL."""
    seen = set()
    new_articles = []
    skipped = 0
    for art in articles:
        url = art.get("url", "")
        if not url:
            continue
        norm = normalize_url(url)
        if norm in existing_urls or url in existing_urls:
            skipped += 1
            continue
        if norm in seen:
            skipped += 1
            continue
        seen.add(norm)
        new_articles.append(art)
    return new_articles, skipped


def classify_articles(articles):
    """Apply topic classification to each article."""
    for art in articles:
        title = art.get("title", "")
        abstract = art.get("abstract", "")
        keywords = art.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [k.strip() for k in re.split(r"[,，]", keywords) if k.strip()]
            art["keywords"] = keywords
        topics, primary = classify(title, abstract, keywords)
        art["topics"] = topics
        art["primary_topic"] = primary
        if not art.get("title_cn"):
            art["title_cn"] = ""
        if not art.get("authors"):
            art["authors"] = "Not stated"
        if not art.get("affiliations"):
            art["affiliations"] = "Not stated"
        if not art.get("abstract"):
            art["abstract"] = "Not available"
        if not art.get("type"):
            art["type"] = "article"
    return articles


def validate_db(db_path):
    """Validate database after update."""
    errors = []
    try:
        with open(db_path, encoding="utf-8") as f:
            db = json.load(f)
    except json.JSONDecodeError as e:
        return [f"JSON 无效: {e}"]

    articles = db.get("articles", [])
    valid_sources = {s["id"] for s in db.get("sources", [])}
    valid_topics = {"corporate_governance", "financial_regulation", "antitrust", "tech_data_ai", "other"}

    urls = [a.get("url", "") for a in articles]
    from collections import Counter
    dupes = {u: c for u, c in Counter(urls).items() if c > 1 and u}
    if dupes:
        errors.append(f"重复 URL: {len(dupes)} 个")

    for i, a in enumerate(articles):
        if not a.get("source_id"):
            errors.append(f"#{i}: 缺少 source_id")
        elif a["source_id"] not in valid_sources:
            errors.append(f"#{i}: source_id={a['source_id']} 不合法")
        if not a.get("url"):
            errors.append(f"#{i}: 缺少 url")
        if not a.get("primary_topic"):
            errors.append(f"#{i}: 缺少 primary_topic")
        elif a["primary_topic"] not in valid_topics:
            errors.append(f"#{i}: primary_topic={a['primary_topic']} 不合法")
        if not isinstance(a.get("authors"), str):
            errors.append(f"#{i}: authors 不是字符串")
        if not isinstance(a.get("affiliations"), str):
            errors.append(f"#{i}: affiliations 不是字符串")

    return errors


def run_update_db(temp_articles_path):
    """Run update_db.py as subprocess."""
    import subprocess
    venv_python = str(PROJECT_DIR / ".venv" / "bin" / "python")
    if not Path(venv_python).exists():
        venv_python = sys.executable
    cmd = [venv_python, str(SCRIPTS_DIR / "update_db.py"), str(temp_articles_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                             env={**os.environ, "PYTHONHOME": "", "PYTHONPATH": ""})
    if result.returncode != 0:
        logging.error(f"update_db.py 失败:\n{result.stderr}")
        return False
    logging.info(f"update_db.py 输出:\n{result.stdout}")
    return True


def run_add_report(temp_report_path):
    """Run add_report.py as subprocess."""
    import subprocess
    venv_python = str(PROJECT_DIR / ".venv" / "bin" / "python")
    if not Path(venv_python).exists():
        venv_python = sys.executable
    cmd = [venv_python, str(SCRIPTS_DIR / "add_report.py"), str(temp_report_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                             env={**os.environ, "PYTHONHOME": "", "PYTHONPATH": ""})
    if result.returncode != 0:
        logging.error(f"add_report.py 失败:\n{result.stderr}")
        return False
    logging.info(f"add_report.py 输出:\n{result.stdout}")
    return True


def main():
    log_file = setup_logging()
    start_time = datetime.now()
    report_id = start_time.strftime("%Y-%m-%d")

    logging.info("=" * 60)
    logging.info("商业法律研究动向 — 周自动化运行开始")
    logging.info(f"报告 ID: {report_id}")
    logging.info(f"开始时间: {start_time.strftime('%Y-%m-%dT%H:%M:%S')}")
    logging.info("=" * 60)

    # 1. Read state
    state = load_state()
    db = load_db()
    since_date = get_since_date(state, db)
    existing_urls = get_existing_urls(db)

    logging.info(f"上次成功运行: {state.get('last_successful_run', 'N/A')}")
    logging.info(f"增量窗口起始: {since_date}")
    logging.info(f"数据库现有文章: {len(db.get('articles', []))} 篇")

    # 2. Scrape
    all_scraped, source_status = run_scrapers(since_date)
    logging.info(f"抓取总计: {len(all_scraped)} 篇原始文章")

    # 3. Filter & dedup
    new_articles, skipped = filter_and_dedup(all_scraped, existing_urls)
    logging.info(f"去重后新增: {len(new_articles)} 篇, 跳过重复: {skipped} 篇")

    # 4. Classify
    new_articles = classify_articles(new_articles)

    # 4.5 Translate (title + abstract + keywords → Chinese)
    if new_articles:
        from utils.translator import enrich_article_with_cn
        logging.info(f"开始翻译 {len(new_articles)} 篇新文章...")
        for i, art in enumerate(new_articles, 1):
            try:
                enrich_article_with_cn(art)
                title_cn = art.get("title_cn", "")
                logging.info(f"  [{i}/{len(new_articles)}] 翻译完成: {title_cn[:40]}")
            except Exception as e:
                logging.warning(f"  [{i}/{len(new_articles)}] 翻译失败: {e}")
        logging.info("翻译步骤完成")

    # 5. Assign report_id
    for art in new_articles:
        art["report_id"] = report_id

    # 6. Determine report period (incremental: since last run)
    if state.get("last_successful_run"):
        last_date = state["last_successful_run"][:10]
    else:
        last_date = since_date
    period_start = last_date
    period_end = start_time.strftime("%Y-%m-%d")

    # Check if report already exists in DB
    report_exists = any(r["id"] == report_id for r in db.get("reports", []))
    report_path = REPORTS_DIR / f"商业法律研究动向_{report_id}.md"

    # If no new articles and report already exists, skip report generation
    if not new_articles and report_exists and report_path.exists():
        logging.info("无新文章且报告已存在，跳过报告生成")
        # Still update state and clean up
        finish_time = datetime.now()
        elapsed = (finish_time - start_time).total_seconds()
        state["last_successful_run"] = finish_time.strftime("%Y-%m-%dT%H:%M:%S")
        state["last_run_started"] = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        state["last_run_finished"] = finish_time.strftime("%Y-%m-%dT%H:%M:%S")
        state["last_new_articles"] = 0
        state["last_duplicate_urls"] = skipped
        state["source_status"] = source_status
        save_state(state)
        logging.info(f"运行完成（增量检查：0 新增，{skipped} 重复）")
        print(f"\n{'=' * 60}")
        print(f"周报路径: {report_path} (未修改)")
        print(f"新增文章数: 0")
        print(f"跳过的重复 URL 数: {skipped}")
        print(f"数据库当前总文章数: {len(db.get('articles', []))}")
        print(f"运行时间: {elapsed:.1f}s")
        failed_sources = [s for s, st in source_status.items() if st == "FAILED"]
        if failed_sources:
            print(f"异常: 以下来源抓取失败: {', '.join(failed_sources)}")
        else:
            print("异常: 无")
        print(f"{'=' * 60}")
        return 0

    # 6.5 No 7-day window — report uses only new_articles from this run

    # 7. Generate report metadata
    trends = []
    if new_articles:
        from collections import Counter
        topic_dist = Counter(a.get("primary_topic", "other") for a in new_articles)
        source_dist = Counter(a.get("source_id", "") for a in new_articles)
        active_sources = "、".join(SOURCE_NAMES.get(s, s) for s in source_dist if source_dist[s] > 0)
        topic_str = "、".join(f"{TOPIC_NAMES.get(t, t)}（{c}篇）" for t, c in topic_dist.most_common(3))
        trends.append(f"本周十一大来源共新增{len(new_articles)}篇文章，来自{active_sources}，主题分布以{topic_str}为主。")
        for topic_id in TOPIC_ORDER:
            topic_arts = [a for a in new_articles if topic_id in (a.get("topics") or [])]
            if topic_arts:
                topic_name = TOPIC_NAMES[topic_id]
                sources_in_topic = set(a.get("source_id") for a in topic_arts)
                source_str = "、".join(SOURCE_NAMES.get(s, s) for s in sources_in_topic)
                titles = [a.get("title_cn") or a.get("title", "") for a in topic_arts]
                titles_short = [t[:50] for t in titles[:3]]
                trends.append(
                    f"{topic_name}领域新增{len(topic_arts)}篇，来自{source_str}。"
                    f"本期重点议题包括{'；'.join(titles_short)}{'等' if len(titles) > 3 else ''}。"
                )
    else:
        trends.append("本周十一大来源均无新增文章，可能是各机构发布周期所致。")
    failed = [s for s, st in source_status.items() if st == "FAILED"]
    if failed:
        failed_names = "、".join(SOURCE_NAMES.get(s, s) for s in failed)
        trends.append(f"本周{failed_names}来源无法访问，未完成抓取。")

    report_meta = generate_report_metadata(report_id, period_start, period_end, new_articles, trends)

    # 8. Write temp files
    with TEMP_REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report_meta, f, ensure_ascii=False, indent=2)
    with TEMP_ARTICLES_PATH.open("w", encoding="utf-8") as f:
        json.dump(new_articles, f, ensure_ascii=False, indent=2)
    logging.info(f"临时文件已写入: {TEMP_REPORT_PATH}, {TEMP_ARTICLES_PATH}")

    # 9. Generate Markdown report
    report_md = generate_report(report_id, period_start, period_end, new_articles, source_status, start_time)
    REPORTS_DIR.mkdir(exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        f.write(report_md)
    logging.info(f"周报已生成: {report_path}")

    # 10. Add report metadata to DB
    if not report_exists:
        ok = run_add_report(TEMP_REPORT_PATH)
        if not ok:
            logging.error("周报元数据入库失败，但继续更新文章")

    # 11. Update article DB
    if new_articles:
        ok = run_update_db(TEMP_ARTICLES_PATH)
        if not ok:
            logging.error("文章数据库更新失败，保留临时文件")
            # Don't clean up temp files on failure
            finish_time = datetime.now()
            state["last_run_started"] = start_time.strftime("%Y-%m-%dT%H:%M:%S")
            state["last_run_finished"] = finish_time.strftime("%Y-%m-%dT%H:%M:%S")
            state["source_status"] = source_status
            save_state(state)
            logging.error("运行结束（数据库更新失败）")
            return 1

    # 12. Validate DB
    errors = validate_db(DB_PATH)
    if errors:
        logging.warning(f"数据库验证发现 {len(errors)} 个问题:")
        for e in errors[:10]:
            logging.warning(f"  - {e}")
    else:
        logging.info("数据库验证通过")

    # 13. Clean up temp files (only on success)
    for p in [TEMP_REPORT_PATH, TEMP_ARTICLES_PATH]:
        if p.exists():
            p.unlink()
            logging.info(f"已清理: {p}")

    # 14. Reload DB for final count
    db_final = load_db()
    total_articles = len(db_final.get("articles", []))

    # 15. Update state
    finish_time = datetime.now()
    elapsed = (finish_time - start_time).total_seconds()
    state["last_successful_run"] = finish_time.strftime("%Y-%m-%dT%H:%M:%S")
    state["last_run_started"] = start_time.strftime("%Y-%m-%dT%H:%M:%S")
    state["last_run_finished"] = finish_time.strftime("%Y-%m-%dT%H:%M:%S")
    state["last_report_id"] = report_id
    state["last_new_articles"] = len(new_articles)
    state["last_duplicate_urls"] = skipped
    state["source_status"] = source_status
    save_state(state)

    # 16. Deploy
    deploy_ok = False
    deploy_url = ""
    try:
        venv_python = str(PROJECT_DIR / ".venv" / "bin" / "python")
        if not Path(venv_python).exists():
            venv_python = sys.executable
        cmd = [venv_python, str(SCRIPTS_DIR / "deploy.py"), "--push"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                                 cwd=str(PROJECT_DIR),
                                 env={**os.environ, "PYTHONHOME": "", "PYTHONPATH": ""})
        if result.returncode == 0:
            deploy_ok = True
            deploy_url = result.stdout.strip().split("\n")[-1].replace("部署成功: ", "")
            logging.info(f"部署成功: {deploy_url}")
        else:
            logging.warning(f"部署失败（不影响数据完整性）: {result.stderr[:200]}")
    except Exception as e:
        logging.warning(f"部署异常（不影响数据完整性）: {e}")

    # 17. Final summary
    logging.info("=" * 60)
    logging.info("运行完成")
    logging.info(f"  新增文章数: {len(new_articles)}")
    logging.info(f"  跳过重复: {skipped}")
    logging.info(f"  数据库总文章数: {total_articles}")
    logging.info(f"  来源状态: {source_status}")
    logging.info(f"  运行耗时: {elapsed:.1f}s")
    logging.info(f"  周报路径: {report_path}")
    logging.info(f"  日志文件: {log_file}")
    if deploy_ok:
        logging.info(f"  部署: {deploy_url}")
    else:
        logging.info("  部署: 未完成（需手动配置 git remote）")
    logging.info("=" * 60)

    # Print summary for console
    print(f"\n{'=' * 60}")
    print(f"周报路径: {report_path}")
    print(f"新增文章数: {len(new_articles)}")
    print(f"跳过的重复 URL 数: {skipped}")
    print(f"数据库当前总文章数: {total_articles}")
    print(f"运行时间: {elapsed:.1f}s")
    if deploy_ok:
        print(f"网页公网链接: {deploy_url}")
    else:
        print(f"网页公网链接: 未部署（需配置 git remote）")
    failed_sources = [s for s, st in source_status.items() if st == "FAILED"]
    if failed_sources:
        print(f"异常: 以下来源抓取失败: {', '.join(failed_sources)}")
    else:
        print("异常: 无")
    print(f"{'=' * 60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
