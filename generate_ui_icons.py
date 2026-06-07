#!/usr/bin/env python3
"""
UI 헤딩/버튼용 컬러 아이콘을 생성합니다 (목업의 라인 아이콘 스타일).
icons/ 폴더에 link, gear, folder, video, activity, folder_blue, download,
help 아이콘 PNG 를 만듭니다. 4배 슈퍼샘플링 후 축소해 가장자리를 매끄럽게.

    pip install Pillow
    python generate_ui_icons.py
"""

import os
import math
from PIL import Image, ImageDraw

OUT = "icons"
SS = 4          # 슈퍼샘플링 배율
FINAL = 44      # 최종 픽셀 크기
S = FINAL * SS

# 팔레트 (목업 톤)
BLUE = (59, 130, 246, 255)
INDIGO = (79, 99, 216, 255)
YELLOW = (245, 176, 32, 255)
GREEN = (16, 185, 129, 255)
GRAY = (148, 167, 184, 255)
WHITE = (255, 255, 255, 255)


def canvas():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def save(img, name):
    os.makedirs(OUT, exist_ok=True)
    img = img.resize((FINAL, FINAL), Image.LANCZOS)
    img.save(os.path.join(OUT, name + ".png"))
    print("  icons/%s.png" % name)


def pill_ring(size, color, lw):
    """수평 알약(라운드 사각형) 링 한 개를 그린 RGBA 이미지."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = int(size * 0.16)
    box = [m, int(size * 0.34), size - m, int(size * 0.66)]
    r = (box[3] - box[1]) // 2
    d.rounded_rectangle(box, radius=r, outline=color, width=lw)
    return img


def icon_link():
    lw = int(S * 0.085)
    ring = pill_ring(int(S * 0.78), BLUE, lw).rotate(45, expand=True, resample=Image.BICUBIC)
    img, _ = canvas()
    off = int(S * 0.11)
    cx = (S - ring.width) // 2
    cy = (S - ring.height) // 2
    img.alpha_composite(ring, (cx - off, cy - off))
    img.alpha_composite(ring, (cx + off, cy + off))
    save(img, "link")


def icon_gear():
    img, d = canvas()
    cx = cy = S / 2
    teeth = 8
    r_out = S * 0.40
    r_in = S * 0.30
    pts = []
    steps = teeth * 2
    tooth_w = 0.30  # 톱니 폭 비율
    for i in range(steps):
        a0 = (i / steps) * 2 * math.pi
        r = r_out if i % 2 == 0 else r_in
        # 톱니 평평하게: 각 구간 양 끝 점
        a1 = a0 + (2 * math.pi / steps) * (0.5 - tooth_w / 2)
        a2 = a0 + (2 * math.pi / steps) * (0.5 + tooth_w / 2)
        pts.append((cx + r * math.cos(a1), cy + r * math.sin(a1)))
        pts.append((cx + r * math.cos(a2), cy + r * math.sin(a2)))
    d.polygon(pts, fill=INDIGO)
    # 가운데 구멍
    hr = S * 0.135
    d.ellipse([cx - hr, cy - hr, cx + hr, cy + hr], fill=(0, 0, 0, 0))
    # 구멍을 투명하게: 다시 그리기 위해 마스크 방식
    img2, d2 = canvas()
    d2.polygon(pts, fill=INDIGO)
    hole = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    dh = ImageDraw.Draw(hole)
    dh.ellipse([cx - hr, cy - hr, cx + hr, cy + hr], fill=(255, 255, 255, 255))
    # 구멍 빼기
    r2, g2, b2, a2 = img2.split()
    hr_, hg_, hb_, ha_ = hole.split()
    from PIL import ImageChops
    a2 = ImageChops.subtract(a2, ha_)
    img2 = Image.merge("RGBA", (r2, g2, b2, a2))
    save(img2, "gear")


def _folder(color):
    img, d = canvas()
    # 탭
    d.rounded_rectangle([S*0.16, S*0.26, S*0.50, S*0.40], radius=int(S*0.05), fill=color)
    # 본체
    d.rounded_rectangle([S*0.14, S*0.34, S*0.86, S*0.74], radius=int(S*0.07), fill=color)
    return img


def icon_folder():
    save(_folder(YELLOW), "folder")


def icon_folder_blue():
    save(_folder(BLUE), "folder_blue")


def icon_video():
    img, d = canvas()
    # 둥근 사각 화면
    d.rounded_rectangle([S*0.16, S*0.28, S*0.84, S*0.72], radius=int(S*0.11),
                        outline=GREEN, width=int(S*0.085))
    # 재생 삼각형
    d.polygon([(S*0.44, S*0.40), (S*0.44, S*0.60), (S*0.62, S*0.50)], fill=GREEN)
    save(img, "video")


def icon_activity():
    img, d = canvas()
    pts = [(S*0.14, S*0.52), (S*0.34, S*0.52), (S*0.44, S*0.30),
           (S*0.58, S*0.70), (S*0.68, S*0.48), (S*0.86, S*0.48)]
    d.line(pts, fill=BLUE, width=int(S*0.075), joint="curve")
    save(img, "activity")


def icon_download():
    img, d = canvas()
    # 화살표 기둥
    sw = S * 0.13
    d.rounded_rectangle([S/2 - sw/2, S*0.24, S/2 + sw/2, S*0.56],
                        radius=int(sw*0.4), fill=WHITE)
    # 화살촉
    d.polygon([(S*0.34, S*0.50), (S*0.66, S*0.50), (S*0.50, S*0.68)], fill=WHITE)
    # 받침 트레이
    lw = int(S*0.075)
    d.line([(S*0.30, S*0.66), (S*0.30, S*0.76), (S*0.70, S*0.76), (S*0.70, S*0.66)],
           fill=WHITE, width=lw, joint="curve")
    save(img, "download")


def icon_help():
    img, d = canvas()
    d.ellipse([S*0.12, S*0.12, S*0.88, S*0.88], outline=GRAY, width=int(S*0.07))
    # 물음표 (텍스트 대신 곡선 근사) - 간단히 점+호
    d.arc([S*0.34, S*0.28, S*0.66, S*0.56], start=160, end=20, fill=GRAY, width=int(S*0.07))
    d.line([(S*0.50, S*0.52), (S*0.50, S*0.62)], fill=GRAY, width=int(S*0.07))
    d.ellipse([S*0.46, S*0.68, S*0.54, S*0.76], fill=GRAY)
    save(img, "help")


def main():
    print("[icons] generating...")
    icon_link()
    icon_gear()
    icon_folder()
    icon_folder_blue()
    icon_video()
    icon_activity()
    icon_download()
    icon_help()
    print("[icons] done.")


if __name__ == "__main__":
    main()
