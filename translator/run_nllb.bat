@echo off
chcp 65001 >nul
rem NLLB-200 번역기: 의존성 설치 후 실행 (빌드 없이 바로 사용 권장)
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [오류] python 을 찾을 수 없습니다. https://www.python.org 에서 설치하세요.
    echo        설치 시 "Add Python to PATH" 체크 필수.
    pause
    exit /b 1
)

echo transformers / torch / sentencepiece 설치 확인 중...
echo (torch 는 용량이 커서 처음엔 시간이 좀 걸립니다)
python -m pip install --upgrade transformers torch sentencepiece
if errorlevel 1 (
    echo [오류] 패키지 설치 실패.
    pause
    exit /b 1
)

echo 번역기 실행... (처음 번역 시 모델 ~2.4GB 다운로드)
python translator_nllb.py
