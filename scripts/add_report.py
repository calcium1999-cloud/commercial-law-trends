#!/usr/bin/env python3
"""
add_report.py — 将新周报元数据添加到 articles.json 和 index.html 的 reports 数组

用法:
    python3 add_report.py <report.json>

职责:
  1. 读 database/articles.json
  2. 读入报告 JSON
  3. 按 id 去重（同 id 报告不重复入库）
  4. 追加到 reports 数组
  5. 写回 database/articles.json
  6. 替换 index.html 中 <script id="db-data"> 块

报告 JSON 格式:
{
  "id": "2026-07-28",
  "date": "2026-07-28",
  "period_start": "2026-07-25",
  "period_end": "2026-07-27",
  "title": "商业法律研究动向",
  "summary": "本周六大来源共新增...",
  "trends": ["趋势一", "趋势二"]
}
"""
import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "database" / "articles.json"
HTML_PATH = PROJECT_DIR / "index.html"


def load_db():
    with DB_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def load_report(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data


def validate_report(rep: dict) -> list[str]:
    errors = []
    required = ["id", "date", "period_start", "period_end", "title", "summary", "trends"]
    for field in required:
        if not rep.get(field):
            errors.append(f"缺少必填字段 {field!r}")
    if isinstance(rep.get("trends"), list) and len(rep["trends"]) == 0:
        errors.append("trends 数组不能为空")
    return errors


def update_html(db: dict):
    html = HTML_PATH.read_text(encoding="utf-8")
    pretty = json.dumps(db, ensure_ascii=False, indent=2)
    new_block = (
        '<script id="db-data" type="application/json">\n'
        + pretty
        + '\n</script>'
    )
    pattern = re.compile(
        r'<script id="db-data" type="application/json">.*?</script>',
        re.DOTALL,
    )
    # Use a callable replacement so JSON backslashes (for example ``\\n`` in
    # report text) are not interpreted as regex replacement escapes.
    new_html, n = pattern.subn(lambda _match: new_block, html, count=1)
    if n != 1:
        raise RuntimeError(
            f"未在 index.html 中找到 <script id=\"db-data\"> 块（实际匹配 {n} 次）"
        )
    HTML_PATH.write_text(new_html, encoding="utf-8")


def normalize_period_start(report: dict, reports: list[dict]) -> dict:
    """若新报告的 period_start 与上一期重叠，自动后移至上一期 end 次日，消除标题重叠。"""
    if not reports:
        return report
    prev = max(reports, key=lambda r: r["date"])
    prev_end = datetime.strptime(prev["period_end"], "%Y-%m-%d")
    cur_start = datetime.strptime(report["period_start"], "%Y-%m-%d")
    if cur_start <= prev_end:
        new_start = (prev_end + timedelta(days=1)).strftime("%Y-%m-%d")
        cur_end = datetime.strptime(report["period_end"], "%Y-%m-%d")
        if new_start > report["period_end"]:
            print(f"  ⚠️  period_start 修正会导致 start>end，保留原值 {report['period_start']}")
        else:
            print(f"  修正 period_start: {report['period_start']} → {new_start}（消除与 {prev['id']} 的标题重叠）")
            report["period_start"] = new_start
    return report


def maintain_monthly(db: dict, report: dict):
    """将新报告归入对应月份分组，并提示月报按语是否需要更新。"""
    month = (report.get("date") or report["id"])[:7]
    label = f"{month[:4]}年{int(month[5:7])}月"
    monthly = db.setdefault("monthly_reports", [])
    entry = next((m for m in monthly if m.get("month") == month), None)
    if entry is None:
        entry = {
            "id": month,
            "month": month,
            "label": label,
            "report_ids": [report["id"]],
            "summary": "",
            "trends": []
        }
        monthly.append(entry)
        monthly.sort(key=lambda m: m["month"])
        print(f"  新建月度分组: {label}（月报按语待填写）")
    else:
        if report["id"] not in entry["report_ids"]:
            entry["report_ids"].append(report["id"])
            entry["report_ids"].sort()
        print(f"  归入月度分组: {label}")
    if not entry.get("summary") or not entry.get("trends"):
        print(f"  ⚠️  请为该月填写月报按语（database/articles.json → monthly_reports → {month}）")


def main():
    ap = argparse.ArgumentParser(description="向数据库添加周报元数据")
    ap.add_argument("report_file", type=Path, help="报告 JSON 文件路径")
    ap.add_argument("--dry-run", action="store_true", help="只校验，不实际写入")
    args = ap.parse_args()

    if not args.report_file.exists():
        print(f"ERROR: 文件不存在: {args.report_file}", file=sys.stderr)
        sys.exit(1)

    print(f"加载数据库: {DB_PATH}")
    db = load_db()

    existing_ids = {r["id"] for r in db["reports"]}
    print(f"  已有 {len(db['reports'])} 期周报: {sorted(existing_ids)}")

    print(f"加载新报告: {args.report_file}")
    report = load_report(args.report_file)
    print(f"  报告 id: {report['id']}")

    # 校验
    errors = validate_report(report)
    if errors:
        print("\n校验失败:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    print("  校验通过")

    # 去重
    if report["id"] in existing_ids:
        print(f"  跳过: 报告 id={report['id']!r} 已存在，不重复入库")
        return

    # 自动修正 period_start，消除与上一期的标题重叠
    report = normalize_period_start(report, db["reports"])

    # 维护月度分组
    maintain_monthly(db, report)

    # 排序插入（按日期顺序）
    db["reports"].append(report)
    db["reports"].sort(key=lambda r: r["date"])
    db["meta"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    if args.dry_run:
        print("\n[DRY RUN] 不写入任何文件。")
        return

    # 写入数据库
    DB_PATH.write_text(
        json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n已更新: {DB_PATH}")

    # 写入 HTML
    update_html(db)
    print(f"已更新: {HTML_PATH}")

    print(f"\n完成。周报总数: {len(db['reports'])}")


if __name__ == "__main__":
    main()
