#!/usr/bin/env python3
"""
PyInstaller 로 youtube_downloader.py 를 단일 실행파일로 빌드합니다.

사용법:
    pip install -r requirements-youtube.txt
    python build_exe.py

결과물:
    dist/YouTubeDownloader(.exe)   ← 더블클릭으로 실행되는 단독 실행파일

ffmpeg 포함하기 (선택):
    고화질 병합/MP3 변환을 실행파일 안에 포함하려면, ffmpeg(.exe) 를
    이 스크립트와 같은 폴더에 두고 빌드하면 자동으로 번들됩니다.
"""

import os
import sys
import PyInstaller.__main__

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "youtube_downloader.py")


def main():
    args = [
        SCRIPT,
        "--name=YouTubeDownloader",
        "--onefile",       # 단일 실행파일
        "--noconsole",     # GUI 앱 (콘솔 창 숨김)
        "--clean",
        "--noconfirm",
    ]

    # 같은 폴더에 ffmpeg 가 있으면 실행파일에 함께 번들
    ffmpeg_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    ffmpeg_path = os.path.join(HERE, ffmpeg_name)
    if os.path.exists(ffmpeg_path):
        sep = ";" if os.name == "nt" else ":"
        args.append(f"--add-binary={ffmpeg_path}{sep}.")
        print(f"[build] ffmpeg 포함: {ffmpeg_path}")
    else:
        print("[build] ffmpeg 미포함 (시스템 PATH 의 ffmpeg 를 사용하거나 단일 파일 모드 이용)")

    print("[build] PyInstaller 실행:", " ".join(args))
    PyInstaller.__main__.run(args)
    print("\n[build] 완료! dist/ 폴더의 실행파일을 확인하세요.")


if __name__ == "__main__":
    sys.exit(main())
