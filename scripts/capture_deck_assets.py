#!/usr/bin/env python3
"""截取商业法律研究动向网页各板块真实界面，供发布会PPT使用。"""
import subprocess, time, os, sys
from playwright.sync_api import sync_playwright

ROOT = "/Users/endofmay/Documents/博士/商法研究趋势"
OUT = os.path.join(ROOT, "deck-assets")
os.makedirs(OUT, exist_ok=True)
PORT = 8791

server = subprocess.Popen(
    [sys.executable, "-m", "http.server", str(PORT), "--directory", ROOT],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
time.sleep(1.5)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1200}, device_scale_factor=2)
        page.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="networkidle")
        page.wait_for_timeout(3000)
        try:
            page.evaluate("document.fonts.ready.then(()=>true)")
        except Exception:
            pass
        page.wait_for_timeout(1000)

        def shot(sel, name, pad=0):
            el = page.query_selector(sel)
            if not el:
                print(f"MISS {sel}"); return
            el.scroll_into_view_if_needed()
            page.wait_for_timeout(800)
            el.screenshot(path=os.path.join(OUT, name))
            print("OK", name)

        # 1) 顶部 Header
        shot("header#siteHeader", "01-header.png")
        # 2) 统计条
        shot("#statsBar", "02-stats.png")
        # 3) 全部视图：主题分布条形图 + 词云
        page.evaluate("""() => {
            const el = document.querySelector('#reportList .filter-item');
            if (el) el.scrollIntoView();
        }""")
        page.evaluate("window.scrollTo(0,0)")
        page.wait_for_timeout(500)
        shot("#trendsChart", "03-chart-wordcloud.png")
        # 4) 侧边栏（检索/周报/信源/主题）
        shot("aside", "04-sidebar.png")
        # 5) 文章列表（展开第一张卡片后，逐张截取前两张卡片）
        page.evaluate("""() => {
            const c = document.querySelector('#articlesList .article-card');
            if (c) c.classList.add('expanded');
        }""")
        page.wait_for_timeout(1000)
        cards = page.query_selector_all("#articlesList .article-card")
        for i, c in enumerate(cards[:2]):
            c.scroll_into_view_if_needed(); page.wait_for_timeout(500)
            c.screenshot(path=os.path.join(OUT, f"05-article-{i+1}.png"))
            print(f"OK 05-article-{i+1}.png")
        # 6) 单期周报视图：本期按语 + 下载按钮
        page.evaluate("""() => {
            const items = document.querySelectorAll('#reportList .filter-item');
            if (items.length > 1) items[1].click(); else if (items.length) items[0].click();
        }""")
        page.wait_for_timeout(1500)
        shot("#trendsSection", "06-trends-narrative.png")
        # 7) 页脚信源
        shot("footer", "07-footer.png")
        # 8) 整页长图（回到全部视图）
        page.evaluate("""() => {
            const items = document.querySelectorAll('#reportList .filter-item');
            if (items.length) items[0].click();
        }""")
        page.wait_for_timeout(1500)
        page.evaluate("window.scrollTo(0,0)")
        page.wait_for_timeout(800)
        page.screenshot(path=os.path.join(OUT, "08-fullpage.png"), full_page=True)
        print("OK 08-fullpage.png")
        browser.close()
finally:
    server.terminate()
print("DONE ->", OUT)
