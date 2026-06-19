@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

rem ============================================================
rem  로컬 한영 번역기 - 윈도우 EXE 빌드 스크립트
rem  더블클릭하면: PyInstaller 설치 -> exe 빌드 -> 바탕화면 복사
rem ============================================================

cd /d "%~dp0"

echo.
echo ====== 로컬 한영 번역기 EXE 빌드 시작 ======
echo.

rem --- 1. 파이썬 확인 ---
where python >nul 2>nul
if errorlevel 1 (
    echo [오류] python 을 찾을 수 없습니다.
    echo        https://www.python.org 에서 파이썬을 설치하고
    echo        설치 시 "Add Python to PATH" 를 체크하세요.
    pause
    exit /b 1
)

echo [1/4] PyInstaller 설치/업데이트 중...
python -m pip install --upgrade pip >nul
python -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo [오류] PyInstaller 설치에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo [2/4] EXE 빌드 중... (몇 분 걸릴 수 있습니다)
python -m PyInstaller --noconfirm --onefile --windowed ^
    --name "KoEnTranslator" translator.py
if errorlevel 1 (
    echo [오류] 빌드에 실패했습니다.
    pause
    exit /b 1
)

set "EXE=%~dp0dist\KoEnTranslator.exe"
if not exist "%EXE%" (
    echo [오류] 빌드 결과물을 찾을 수 없습니다: %EXE%
    pause
    exit /b 1
)

echo.
echo [3/4] 바탕화면으로 복사 중...
rem OneDrive 바탕화면도 고려해 USERPROFILE\Desktop 사용
set "DESKTOP=%USERPROFILE%\Desktop"
if not exist "%DESKTOP%" set "DESKTOP=%USERPROFILE%\OneDrive\Desktop"
copy /Y "%EXE%" "%DESKTOP%\한영번역기.exe" >nul
if errorlevel 1 (
    echo [경고] 바탕화면 복사에 실패했습니다. dist 폴더의 exe를 직접 사용하세요.
) else (
    echo        복사 완료: %DESKTOP%\한영번역기.exe
)

echo.
echo [4/4] 완료!
echo.
echo  - 바탕화면의 "한영번역기.exe" 를 더블클릭하면 실행됩니다.
echo  - 단, Ollama 가 실행 중이어야 번역이 동작합니다.
echo    (https://ollama.com 설치 후  ollama pull qwen2.5:7b )
echo.
pause
