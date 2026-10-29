"""아이차트 주간 순위 → Claude 카드뉴스 문구 → 엑셀 저장 (시연 예제)

실행: .venv\\Scripts\\python.exe t01_ichart_demo.py
결과: output/ichart_YYYY-MM-DD.xlsx (순위 시트, 카드뉴스 시트)
"""
import json
import os
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

import anthropic
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ── 경로: 어디서 실행해도 이 파일이 있는 폴더가 기준 ──
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")  # ANTHROPIC_API_KEY 읽기

# ── 수집할 주소 ──
ICHART_URL = os.getenv("ICHART_URL", "https://www.ichart.kr/rank")
CHANGE_MARK = {"up": "▲", "down": "▼", "noChange": "-"}
TOP_N = 10

# ── Claude 설정 (모델 이름은 수업 전 docs.claude.com에서 확인) ──
MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
SOURCE = "출처: 아이차트(ichart.kr)"




# ── 1. 수집: 주소 → HTML 글자 ──
res = requests.get(ICHART_URL, headers=HEADERS, timeout=10)
res.encoding = "utf-8"
html = res.text


# ── 2. 추출: HTML 글자 → 순위 표 ──
soup = BeautifulSoup(html, "html.parser")
# "iChart Ranking" 영역만 (선택자는 F12로 확인)
area = soup.select_one('[aria-labelledby="ranking-title"]') or soup

rows = []
# 곡 하나 = /song/번호 링크
for a in area.select('a[href*="/song/"]'):
    # 링크(a) 안의 구조: span=순위, h3=곡명, p=가수, strong=점수, img=변동 아이콘
    rank = a.select_one("span").get_text(strip=True)
    title = a.select_one("h3").get_text(strip=True)
    artist = a.select_one("p").get_text(strip=True)
    score = a.select_one("strong").get_text(strip=True)

    # 변동: 아이콘 alt(up/down/noChange) → ▲▼-, 아이콘 옆 숫자를 붙여 "▲1"
    icon = a.select_one("img")
    mark = CHANGE_MARK.get(icon["alt"], icon["alt"])
    change = mark + icon.parent.get_text(strip=True)

    rows.append({
        "순위": rank,
        "곡명": title,
        "가수": artist,
        "점수": score,
        "변동": change,
        "링크": urljoin(ICHART_URL, a["href"]),
    })
    if len(rows) == TOP_N:
        break

df = pd.DataFrame(rows)
print(df)


# ── 3. 변환: 순위 표 → Claude → 카드뉴스 문구(JSON) ──

PROMPT = """아이차트 주간 음악 순위다.
인스타그램 카드뉴스 문구를
JSON으로만 답할 것.
{{"제목": "...",
 "카드": ["1장 문구", "..."],
 "해시태그": ["#..."]}}
카드는 3~5장, 장마다 두 문장 이내.
순위표에 없는 사실은 쓰지 않기.

{table}""" 

table = df[["순위", "곡명", "가수"]].to_string(index=False)
client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 사용
msg = client.messages.create(
    model=MODEL,
    max_tokens=4096,  # 생각(thinking)까지 포함한 길이라 넉넉히
    messages=[{"role": "user", "content": PROMPT.format(table=table)}],
)

# 답에는 생각(thinking) 블록이 먼저 올 수 있으니, 글(text) 블록만 골라 꺼내기
text = ""
for block in msg.content:
    if block.type == "text":
        text = block.text

# ```json 울타리를 벗기고 JSON으로 읽기
text = text.strip().removeprefix("```json").removeprefix("```")
text = text.removesuffix("```").strip()
card = json.loads(text)
print(card)


# ── 4. 저장 준비: 카드뉴스 → 표 (출처·AI 초안 표시 포함) ──
card_rows = [("제목", card["제목"])]
for i, line in enumerate(card["카드"], start=1):
    card_rows.append((f"카드 {i}", line))
card_rows.append(("해시태그", " ".join(card["해시태그"])))
card_rows.append(("출처", SOURCE))
card_rows.append(("비고", "AI 생성 초안 · 검수 후 게시"))
card_df = pd.DataFrame(card_rows, columns=["구분", "문구"])


# ── 5. 저장: output/ichart_YYYY-MM-DD.xlsx 에 시트 두 개 ──
out_dir = BASE_DIR / "output"
out_dir.mkdir(exist_ok=True)
today = date.today().strftime("%Y-%m-%d")
path = out_dir / f"ichart_{today}.xlsx"
with pd.ExcelWriter(path) as writer:
    df.to_excel(writer, sheet_name="순위", index=False)
    card_df.to_excel(writer, sheet_name="카드뉴스", index=False)

print("저장 완료:", path)
