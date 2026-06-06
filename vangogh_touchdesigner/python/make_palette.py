#!/usr/bin/env python3
"""
고흐 '별이 빛나는 밤' 팔레트 CLUT(룩업 램프) 생성기.

밝기(0=어두움 -> 1=밝음) 순서로 색이 나열된 가로 1픽셀 높이의 PNG를 만든다.
TouchDesigner 의 [Movie File In TOP] 으로 불러와 04_palette.frag 의
sTD2DInputs[1] 에 연결하면, 입력 밝기로 이 램프를 룩업해 색을 통일한다.

사용법:
    python make_palette.py                 # vangogh_palette.png (256x1)
    python make_palette.py --width 512 --out my.png

의존성: numpy, pillow  (pip install numpy pillow)
"""

import argparse
import numpy as np
from PIL import Image

# 밝기 위치(0~1) -> RGB(0~255). 어두운 곳에서 밝은 곳 순서.
# 별이 빛나는 밤의 색 흐름: 짙은 남색 -> 코발트 -> 청록 -> 크롬옐로 -> 흰노랑
STOPS = [
    (0.00, (8,   12,  40)),    # 거의 검은 인디고
    (0.20, (16,  28,  74)),    # 딥 인디고
    (0.40, (29,  90, 141)),    # 코발트 블루
    (0.58, (53, 138, 160)),    # 청록 (휘감기는 하늘)
    (0.74, (180, 170,  90)),   # 황토/올리브
    (0.88, (243, 202,  59)),   # 크롬 옐로 (별빛)
    (1.00, (255, 244, 200)),   # 가장 밝은 노란 흰빛
]


def build_ramp(width: int) -> np.ndarray:
    pos = np.array([s[0] for s in STOPS])
    cols = np.array([s[1] for s in STOPS], dtype=float)
    xs = np.linspace(0.0, 1.0, width)
    ramp = np.empty((width, 3), dtype=np.uint8)
    for c in range(3):
        ramp[:, c] = np.clip(np.interp(xs, pos, cols[:, c]), 0, 255).astype(np.uint8)
    return ramp.reshape(1, width, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=256, help="램프 가로 해상도")
    ap.add_argument("--out", default="vangogh_palette.png", help="출력 PNG 경로")
    args = ap.parse_args()

    img = build_ramp(args.width)
    Image.fromarray(img, "RGB").save(args.out)
    print(f"팔레트 저장 완료: {args.out}  ({args.width}x1)")


if __name__ == "__main__":
    main()
