@echo off
chcp 65001 >nul
rem ============================================================
rem  NLLB-200 번역기 실행 (전용 가상환경 사용)
rem  회원님의 기존 파이썬/torch 환경을 건드리지 않도록 .venv_nllb 안에
rem  필요한 패키지만 따로 설치합니다. (torchvision 충돌 방지)
rem ============================================================
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [오류] python 을 찾을 수 없습니다. https://www.python.org 에서 설치하세요.
    echo        설치 시 "Add Python to PATH" 체크 필수.
    pause
    exit /b 1
)

if not exist ".venv_nllb\Scripts\python.exe" (
    echo 전용 가상환경(.venv_nllb) 생성 중...
    python -m venv .venv_nllb
    if errorlevel 1 (
        echo [오류] 가상환경 생성 실패.
        pause
        exit /b 1
    )
)

echo 가상환경 활성화...
call ".venv_nllb\Scripts\activate.bat"

echo 필요한 패키지 설치 확인 중... (처음엔 torch 다운로드로 시간이 걸립니다)
echo (번역엔 torchvision 이 필요 없으므로 설치하지 않습니다)
python -m pip install --upgrade pip >nul
python -m pip install --upgrade transformers torch sentencepiece
if errorlevel 1 (
    echo [오류] 패키지 설치 실패.
    pause
    exit /b 1
)

echo 번역기 실행... (처음 번역 시 모델 ~2.4GB 다운로드, 이후 오프라인)
python translator_nllb.py

if errorlevel 1 (
    echo.
    echo [안내] 오류로 종료되었습니다. 위 메시지를 확인하세요.
    pause
)
