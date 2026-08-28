from playwright.sync_api import sync_playwright
from pathlib import Path

PROJECT = Path("/Users/endofmay/Documents/博士/商法研究趋势")
HTML = f"file://{PROJECT / 'presentation' / 'xhs_v3.html'}"
OUT = PROJECT / "presentation"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1080, "height": 800})
    page.goto(HTML)
    page.wait_for_timeout(1500)

    p1 = page.query_selector(".poster1")
    if p1:
        p1.screenshot(path=str(OUT / "xhs_v3_poster1.png"), type="png")
        print("poster1 done")

    p2 = page.query_selector(".poster2")
    if p2:
        p2.screenshot(path=str(OUT / "xhs_v3_poster2.png"), type="png")
        print("poster2 done")

    p3 = page.query_selector(".poster3")
    if p3:
        p3.screenshot(path=str(OUT / "xhs_v3_poster3.png"), type="png")
        print("poster3 done")

    browser.close()
    print("All 3 v3 posters exported!")
