"""위비티 공모전 목록 1~3페이지 → 엑셀 저장 (3교시 응용 정답)

실행: .venv\\Scripts\\python.exe t02_wevity_list.py
결과: wevity_공모전.xlsx
"""
import os
import time
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

# ── 경로: 어디서 실행해도 이 파일이 있는 폴더가 기준 ──
BASE_DIR = Path(__file__).parent

# ── 수집할 주소 (수업 전 F12로 확인) ──
WEVITY_URL = os.getenv("WEVITY_URL", "https://www.wevity.com/")
DETAIL_LINK = 'a[href*="gbn=view"]'  # 공모전 하나 = 상세 페이지로 가는 링크
PAGES = range(1, 4)                  # 1~3페이지
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


# ── 1. 수집 + 추출: 페이지마다 주소 → HTML 글자 → 공모전 목록 ──
rows = []
seen = set()  # 이미 담은 링크 (중복 거르기)

for gp in PAGES:
    # 목록 주소: ?c=find&s=1&gp=페이지번호
    params = {"c": "find", "s": "1", "gp": gp}
    res = requests.get(WEVITY_URL, params=params, headers=HEADERS, timeout=10)
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")

    for a in soup.select(DETAIL_LINK):
        title = a.get_text(strip=True)
        link = urljoin(WEVITY_URL, a["href"])

        # 글자 없는 이미지 링크와 중복 링크는 건너뜀
        if title == "" or link in seen:
            continue
        seen.add(link)

        rows.append({
            "페이지": gp,
            "제목": title,
            "링크": link,
        })

    print(gp, "페이지까지", len(rows), "건")
    time.sleep(1)  # 서버 부담 줄이기


# ── 2. 표로 정리 ──
df = pd.DataFrame(rows)
print(df)


# ── 3. 저장: wevity_공모전.xlsx ──
path = BASE_DIR / "wevity_공모전.xlsx"
df.to_excel(path, index=False)

print("저장 완료:", path)
