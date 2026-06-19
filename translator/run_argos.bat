@echo off
chcp 65001 >nul
rem 빌드 없이 바로 실행: argostranslate 설치 후 앱 실행
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [오류] python 을 찾을 수 없습니다. https://www.python.org 에서 설치하세요.
    echo        설치 시 "Add Python to PATH" 체크 필수.
    pause
    exit /b 1
)

echo argostranslate 설치 확인/설치 중...
python -m pip install --upgrade argostranslate
if errorlevel 1 (
    echo [오류] argostranslate 설치 실패.
    pause
    exit /b 1
)

echo 번역기 실행...
python translator_argos.py
