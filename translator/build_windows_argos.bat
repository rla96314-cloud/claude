@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

rem ============================================================
rem  로컬 한영 번역기 (Argos) - 윈도우 EXE 빌드 스크립트
rem  더블클릭: argostranslate+PyInstaller 설치 -> exe 빌드 -> 바탕화면 복사
rem ============================================================
cd /d "%~dp0"

echo.
echo ====== Argos 번역기 EXE 빌드 시작 ======
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [오류] python 을 찾을 수 없습니다. https://www.python.org 에서 설치하세요.
    echo        설치 시 "Add Python to PATH" 체크 필수.
    pause
    exit /b 1
)

echo [1/4] 필요한 패키지 설치 중... (시간이 좀 걸립니다)
python -m pip install --upgrade pip >nul
python -m pip install --upgrade argostranslate pyinstaller
if errorlevel 1 (
    echo [오류] 패키지 설치 실패.
    pause
    exit /b 1
)

echo.
echo [2/4] EXE 빌드 중... (몇 분 걸릴 수 있습니다)
rem argostranslate 는 데이터 파일이 많아 의존 패키지를 통째로 포함시켜야 함
python -m PyInstaller --noconfirm --onefile --windowed ^
    --name "KoEnTranslatorArgos" ^
    --collect-all argostranslate ^
    --collect-all stanza ^
    --collect-all sentencepiece ^
    --collect-all ctranslate2 ^
    translator_argos.py
if errorlevel 1 (
    echo [오류] 빌드 실패. (위 메시지를 확인하세요)
    pause
    exit /b 1
)

set "EXE=%~dp0dist\KoEnTranslatorArgos.exe"
if not exist "%EXE%" (
    echo [오류] 빌드 결과물을 찾을 수 없습니다: %EXE%
    pause
    exit /b 1
)

echo.
echo [3/4] 바탕화면으로 복사 중...
rem 진짜 바탕화면 경로를 PowerShell 로 받아와서 복사 (OneDrive 대응)
for /f "usebackq delims=" %%D in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "DESKTOP=%%D"
if not defined DESKTOP set "DESKTOP=%USERPROFILE%\Desktop"
copy /Y "%EXE%" "%DESKTOP%\한영번역기(Argos).exe" >nul
if errorlevel 1 (
    echo [경고] 바탕화면 복사 실패. dist 폴더의 exe를 직접 사용하세요.
) else (
    echo        복사 완료: %DESKTOP%\한영번역기(Argos).exe
)

echo.
echo [4/4] 완료!
echo  - 바탕화면의 "한영번역기(Argos).exe" 더블클릭으로 실행됩니다.
echo  - 처음 번역할 때만 모델(~100MB)을 인터넷에서 받고, 이후엔 오프라인 동작.
echo.
pause
