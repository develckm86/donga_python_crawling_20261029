"""아이차트 레코드(퍼펙트 올킬) 목록 → Playwright로 스크롤하며 수집 → 엑셀 저장 (4교시)

준비: pip install playwright  →  playwright install chromium
실행: .venv\\Scripts\\python.exe t03_record_playwright.py
결과: ichart_record.xlsx

이 페이지는 '가상 스크롤' 목록이다.
전체 100여 곡 중 화면 근처의 20~30줄만 HTML에 있고,
스크롤하면 위쪽 줄은 지우고 아래쪽 줄을 새로 그린다.
→ 마지막에 HTML을 한 번만 받으면 일부만 남으므로
  조금씩 스크롤하면서 그때그때 읽어 모은다.
"""
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# ── 수집할 주소 ──
URL = "https://www.ichart.kr/record/ichart?recordType=perfect-all-kill"


with sync_playwright() as p:
    # ── 1. 브라우저 열기: 주소 → 목록이 그려질 때까지 기다림 ──
    browser = p.chromium.launch(headless=False)  # False = 크롬 창을 띄워서 보여 줌
    page = browser.new_page()
    page.goto(URL)
    page.wait_for_selector('a[href*="/song/"]', timeout=15000)  # 곡 링크가 나타날 때까지 (최대 15초)

    # ── 2. 스크롤하며 모으기: 지금 화면의 HTML → 곡 정보 ──
    songs = {}  # 모은 곡 {링크: 곡 정보} → 링크가 키라서 같은 곡은 한 번만 남음
    no_new = 0  # 새 곡이 "연속으로" 안 나온 횟수

    # _ 는 "이름 없는 변수"
    #   for i in range(100): 처럼 쓰면 i에 0, 1, 2 … 99 가 차례로 들어가는데,
    #   여기서는 몇 번째인지 쓸 일이 없고 "100번 반복"만 필요하므로
    #   "이 값은 안 쓴다"는 뜻으로 이름 대신 _ 를 쓴다. (i로 써도 동작은 같다)
    for _ in range(100):  # 최대 100번 스크롤 (끝을 못 알아채도 멈추는 안전장치)
        before = len(songs)  # 읽기 전 곡 수 적어 두기

        # 지금 그려진 HTML을 BeautifulSoup으로 읽기 (3교시와 같은 방법)
        soup = BeautifulSoup(page.content(), "html.parser")
        for a in soup.select('a[href*="/song/"]'):  # 곡 하나 = /song/번호 링크
            # 링크(a) 안의 구조: span=순위, h3=곡명, p=가수, time=발매일, 마지막 div=횟수
            if a.select_one("h3") is None:  # 아직 덜 그려진 줄은 건너뜀
                continue

            rank = a.select_one("span").get_text(strip=True)  # 첫 span = 순위 ("01")
            title = a.select_one("h3").get_text(strip=True)
            artist = a.select_one("p").get_text(strip=True)
            # "발매일 : 2025. 06. 20" → ":" 뒤만 → "2025. 06. 20"
            released = a.select_one("time").get_text(strip=True).split(":")[-1].strip()
            count = a.select_one("article > div:last-child span").get_text(strip=True)

            # 같은 링크면 덮어쓰고, 처음 보는 링크면 새로 추가
            songs[a["href"]] = {
                "순위": int(rank),  # "01" → 1 (숫자로 바꿔야 순위순 정렬이 됨)
                "곡명": title,
                "가수": artist,
                "발매일": released,
                "횟수": count,
            }

        print("모은 곡:", len(songs))

        # 곡 수가 그대로면 새 곡 없음 +1, 늘었으면 0으로 되돌림
        if len(songs) == before:
            no_new = no_new + 1
        else:
            no_new = 0

        # 3번 연속 새 곡이 없으면 맨 아래까지 온 것 → 반복 끝
        if no_new >= 3:
            break

        page.mouse.wheel(0, 600)    # 마우스 휠로 아래로 600px (화면 높이보다 작게 → 건너뛰는 줄 없게)
        page.wait_for_timeout(500)  # 새 줄이 그려질 때까지 0.5초 기다리기

    browser.close()


# ── 3. 표로 정리: 순위순으로 정렬 ──
df = pd.DataFrame(songs.values()).sort_values("순위", ignore_index=True)
print(len(df), "곡")
print(df.head())


# ── 4. 저장: 이 파일이 있는 폴더의 ichart_record.xlsx ──
path = Path(__file__).parent / "ichart_record.xlsx"
df.to_excel(path, index=False)

print("저장 완료:", path)
