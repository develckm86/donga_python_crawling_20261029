@echo off
chcp 65001 > nul
rem ============================================================
rem  run_daily.bat : 작업 스케줄러가 매일 실행하는 파일
rem
rem  하는 일 (위에서부터 차례로)
rem    1) 이 파일이 있는 폴더로 이동
rem    2) 가상환경(.venv)의 파이썬으로 SCRIPT 파일 실행
rem    3) 화면에 찍히는 글을 logs\run_bat.log 에 기록
rem
rem  학생이 바꿀 곳: 아래 set SCRIPT= 한 줄만
rem  (맨 위 chcp 65001 = 한글이 깨지지 않게 하는 설정, 지우지 않기)
rem ============================================================

rem 1) 이 파일이 있는 폴더로 이동 (%~dp0 = 이 파일이 있는 폴더)
cd /d "%~dp0"

rem 실행할 파이썬 파일 이름
set SCRIPT=t01_ichart_demo.py

rem 파이썬이 출력하는 한글이 기록 파일에서 깨지지 않게
set PYTHONUTF8=1

rem 기록을 담을 logs 폴더가 없으면 만들기
if not exist logs mkdir logs

rem 2) 3) 파이썬 실행 + 출력을 logs\run_bat.log 끝에 이어 쓰기
rem    >>   = 파일 끝에 이어 쓰기 (> 하나면 덮어씀)
rem    2>&1 = 오류 메시지도 같은 파일에 쓰기
echo ===== %date% %time% 시작 ===== >> logs\run_bat.log
".venv\Scripts\python.exe" %SCRIPT% >> logs\run_bat.log 2>&1

rem 결과 기록: 0 = 성공, 1 = 실패 (작업 스케줄러에도 이 값을 알려 줌)
set RC=%errorlevel%
echo ===== 끝 (결과 %RC%) ===== >> logs\run_bat.log
exit /b %RC%
