@echo off
REM ============================================================
REM  파일 정리 프로그램 - Windows EXE 빌드 스크립트
REM  이 파일을 더블클릭하면 dist\FileOrganizer.exe 가 만들어집니다.
REM  (Python 3.9 이상이 설치돼 있어야 합니다.)
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0"

echo [1/3] PyInstaller 설치 확인 중...
python -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo.
    echo [오류] Python 또는 pip 를 찾을 수 없습니다.
    echo        https://www.python.org 에서 Python 을 먼저 설치하세요.
    pause
    exit /b 1
)

echo.
echo [2/3] GUI 버전 EXE 빌드 중...
python -m PyInstaller --onefile --windowed --name FileOrganizer organize_gui.py
if errorlevel 1 ( echo [오류] 빌드 실패 & pause & exit /b 1 )

echo.
echo [3/3] CLI 버전 EXE 빌드 중...
python -m PyInstaller --onefile --name organize organize.py

echo.
echo ============================================================
echo  완료!  dist 폴더 안에 아래 파일이 생성되었습니다:
echo    - dist\FileOrganizer.exe   (더블클릭하면 창이 열리는 GUI)
echo    - dist\organize.exe        (명령줄용)
echo ============================================================
pause
