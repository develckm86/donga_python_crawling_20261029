# ipynb 쥬피터 노트북과 py 파이썬 파일에서 await 문법이 다르게 사용됩니다.
#l03_ichart_playwright.ipynb 과 아래 코드는 같은 코드입니다.

from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://www.ichart.kr/record/ichart?recordType=perfect-all-kill")
    page.wait_for_selector('a[href*="/song/"]', timeout=15000)
    html = page.content()
    print(html)
    browser.close()