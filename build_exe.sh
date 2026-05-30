#!/usr/bin/env bash
# ============================================================
#  파일 정리 프로그램 - macOS / Linux 실행파일 빌드 스크립트
#  (Windows용 .exe 는 만들 수 없습니다 — Windows에서 build_exe.bat 사용)
#  결과물: dist/FileOrganizer  (해당 OS용 실행 파일)
# ============================================================
set -e
cd "$(dirname "$0")"

echo "[1/2] PyInstaller 설치..."
python3 -m pip install --upgrade pyinstaller

echo "[2/2] 빌드..."
python3 -m PyInstaller --onefile --windowed --name FileOrganizer organize_gui.py
python3 -m PyInstaller --onefile --name organize organize.py

echo
echo "완료! dist/ 폴더를 확인하세요:"
echo "  - dist/FileOrganizer  (GUI)"
echo "  - dist/organize       (CLI)"
