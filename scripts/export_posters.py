from playwright.sync_api import sync_playwright
from pathlib import Path

PROJECT = Path("/Users/endofmay/Documents/博士/商法研究趋势")
HTML = f"file://{PROJECT / 'presentation' / 'xhs_long_images.html'}"
OUT = PROJECT / "presentation"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1080, "height": 800})
    page.goto(HTML)
    page.wait_for_timeout(1500)

    # Poster 1
    p1 = page.query_selector(".poster1")
    if p1:
        p1.screenshot(path=str(OUT / "xhs_poster1_cover.png"), type="png")
        print("poster1 done")

    # Poster 2
    p2 = page.query_selector(".poster2")
    if p2:
        p2.screenshot(path=str(OUT / "xhs_poster2_features.png"), type="png")
        print("poster2 done")

    # Poster 3
    p3 = page.query_selector(".poster3")
    if p3:
        p3.screenshot(path=str(OUT / "xhs_poster3_value.png"), type="png")
        print("poster3 done")

    browser.close()
    print("All 3 posters exported!")
