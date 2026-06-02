#!/usr/bin/env python3
"""
AtomS3 사진기 -> PC 저장 도구

atoms3_camera 펌웨어를 올린 AtomS3R-CAM 에서 사진(JPG)을 받아 PC에 저장합니다.
표준 라이브러리만 사용하므로 추가 설치가 필요 없습니다.

사용법:
    # 사진 한 장 저장
    python atoms3_cam.py --host 192.168.4.1

    # 3초 간격으로 10장 연속 촬영
    python atoms3_cam.py --host 192.168.0.42 --count 10 --interval 3

    # 라이브 영상을 기본 브라우저로 열기
    python atoms3_cam.py --host 192.168.4.1 --view

기본 host 는 핫스팟(AP) 모드 주소인 192.168.4.1 입니다.
집 WiFi(STA) 모드라면 기기 시리얼 로그에 찍힌 IP 를 --host 로 넣으세요.
"""

import argparse
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


def capture_one(host: str, outdir: Path, timeout: float) -> Path:
    """기기에서 /capture 로 JPG 한 장을 받아 타임스탬프 파일로 저장."""
    url = f"http://{host}/capture"
    with urlopen(url, timeout=timeout) as resp:
        data = resp.read()
    if not data:
        raise RuntimeError("빈 응답을 받았습니다 (카메라 초기화 실패?).")

    outdir.mkdir(parents=True, exist_ok=True)
    filename = datetime.now().strftime("atoms3_%Y%m%d_%H%M%S_%f.jpg")
    path = outdir / filename
    path.write_bytes(data)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AtomS3R-CAM 에서 사진을 받아 PC에 저장합니다."
    )
    parser.add_argument(
        "--host",
        default="192.168.4.1",
        help="기기 주소 (기본: 192.168.4.1 - 핫스팟 모드)",
    )
    parser.add_argument(
        "--count", type=int, default=1, help="촬영 장수 (기본: 1)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="연속 촬영 시 간격(초) (기본: 2.0)",
    )
    parser.add_argument(
        "--outdir",
        default="photos",
        help="저장 폴더 (기본: ./photos)",
    )
    parser.add_argument(
        "--timeout", type=float, default=10.0, help="요청 타임아웃(초)"
    )
    parser.add_argument(
        "--view",
        action="store_true",
        help="저장 대신 라이브 영상을 브라우저로 엽니다.",
    )
    args = parser.parse_args()

    if args.view:
        url = f"http://{args.host}/"
        print(f"브라우저에서 라이브 영상 열기: {url}")
        webbrowser.open(url)
        return

    outdir = Path(args.outdir)
    try:
        for i in range(args.count):
            path = capture_one(args.host, outdir, args.timeout)
            print(f"[{i + 1}/{args.count}] 저장됨: {path}")
            if i < args.count - 1:
                time.sleep(args.interval)
    except URLError as exc:
        print(
            f"오류: 기기에 연결할 수 없습니다 ({args.host}). "
            f"\n  - 같은 WiFi/핫스팟에 연결됐는지, --host 주소가 맞는지 확인하세요."
            f"\n  세부: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    except (RuntimeError, OSError) as exc:
        print(f"오류: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
