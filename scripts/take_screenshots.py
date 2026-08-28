from playwright.sync_api import sync_playwright
from pathlib import Path

PROJECT = Path("/Users/endofmay/Documents/博士/商法研究趋势")
OUT = PROJECT / "presentation" / "xhs-assets"
OUT.mkdir(exist_ok=True)

url = f"file://{PROJECT / 'index.html'}"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.goto(url)
    page.wait_for_timeout(2000)

    # 1. Full page screenshot (for poster 1 overview)
    page.screenshot(path=str(OUT / "full_page.png"), full_page=True)
    print("full_page.png done")

    # 2. Top portion with header + stats + trend (cropped to ~900px height)
    page.set_viewport_size({"width": 1400, "height": 850})
    page.screenshot(path=str(OUT / "top_section.png"),
                    clip={"x": 0, "y": 0, "width": 1400, "height": 850})
    print("top_section.png done")

    # 3. Article card area (for feature show)
    page.evaluate("window.scrollTo(0, 500)")
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / "article_cards.png"),
                    clip={"x": 0, "y": 0, "width": 1400, "height": 700})
    print("article_cards.png done")

    # 4. Sidebar closeup
    page.set_viewport_size({"width": 1400, "height": 700})
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / "sidebar.png"),
                    clip={"x": 0, "y": 0, "width": 320, "height": 700})
    print("sidebar.png done")

    # 5. Single article card closeup
    page.set_viewport_size({"width": 1200, "height": 500})
    page.evaluate("window.scrollTo(0, 650)")
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / "single_card.png"),
                    clip={"x": 300, "y": 100, "width": 800, "height": 350})
    print("single_card.png done")

    browser.close()
    print("All screenshots done")
