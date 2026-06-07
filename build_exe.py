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

# Windows 콘솔(cp1252 등)에서도 출력이 깨지거나 멈추지 않도록 UTF-8 로 강제
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

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

    # 같은 폴더에 ffmpeg/ffprobe 가 있으면 실행파일에 함께 번들
    sep = ";" if os.name == "nt" else ":"
    exe_suffix = ".exe" if os.name == "nt" else ""
    bundled_any = False
    for tool in ("ffmpeg", "ffprobe"):
        tool_path = os.path.join(HERE, tool + exe_suffix)
        if os.path.exists(tool_path):
            args.append(f"--add-binary={tool_path}{sep}.")
            print(f"[build] bundling {tool}: {tool_path}")
            bundled_any = True
    if not bundled_any:
        print("[build] ffmpeg not bundled (uses system PATH ffmpeg, or single-file mode)")

    print("[build] running PyInstaller:", " ".join(args))
    PyInstaller.__main__.run(args)
    print("\n[build] done! Check the executable in the dist/ folder.")


if __name__ == "__main__":
    sys.exit(main())
