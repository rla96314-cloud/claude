#!/usr/bin/env python3
"""
앱 아이콘 생성 스크립트.

제공된 디자인(빨간 라운드 사각형 + 흰 YouTube 화면 + 재생 삼각형 +
아래로 향하는 다운로드 화살표 + 받침 트레이)을 그려서
- icon.png (1024x1024, 앱 창 아이콘용)
- icon.ico (멀티 해상도, Windows .exe 아이콘용)
을 생성합니다.

    pip install Pillow
    python generate_icon.py
"""

from PIL import Image, ImageDraw

SIZE = 1024
RED = (242, 38, 30, 255)      # 선명한 YouTube 레드
WHITE = (255, 255, 255, 255)


def rounded_square_mask(size, radius):
    img = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return img


def draw_icon(scale=1):
    s = SIZE * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1) 빨간 라운드 사각형 배경 (살짝 여백)
    margin = int(s * 0.06)
    radius = int(s * 0.235)
    draw.rounded_rectangle(
        [margin, margin, s - margin, s - margin],
        radius=radius,
        fill=RED,
    )

    # 2) 흰색 YouTube 화면 (둥근 사각형)
    screen_w = s * 0.58
    screen_h = s * 0.40
    cx = s / 2
    screen_top = s * 0.215
    screen_box = [
        cx - screen_w / 2,
        screen_top,
        cx + screen_w / 2,
        screen_top + screen_h,
    ]
    draw.rounded_rectangle(screen_box, radius=int(s * 0.085), fill=WHITE)

    # 3) 빨간 재생 삼각형 (화면 중앙)
    tri_cx = cx
    tri_cy = screen_top + screen_h * 0.46
    tri_h = screen_h * 0.42
    tri_w = tri_h * 0.92
    draw.polygon(
        [
            (tri_cx - tri_w * 0.42, tri_cy - tri_h / 2),
            (tri_cx - tri_w * 0.42, tri_cy + tri_h / 2),
            (tri_cx + tri_w * 0.58, tri_cy),
        ],
        fill=RED,
    )

    # 4) 흰색 다운로드 화살표 (화면 아래로 겹쳐서)
    shaft_w = s * 0.135
    shaft_top = screen_top + screen_h * 0.78
    shaft_bottom = s * 0.665
    draw.rounded_rectangle(
        [cx - shaft_w / 2, shaft_top, cx + shaft_w / 2, shaft_bottom],
        radius=int(shaft_w * 0.3),
        fill=WHITE,
    )
    # 화살촉
    head_w = s * 0.28
    head_bottom = s * 0.74
    draw.polygon(
        [
            (cx - head_w / 2, shaft_bottom - s * 0.02),
            (cx + head_w / 2, shaft_bottom - s * 0.02),
            (cx, head_bottom),
        ],
        fill=WHITE,
    )

    # 5) 받침 트레이 (U 모양, 둥근 끝)
    tray_w = s * 0.34
    tray_left = cx - tray_w / 2
    tray_right = cx + tray_w / 2
    tray_top = s * 0.70
    tray_bottom = s * 0.80
    lw = int(s * 0.052)
    # 세로 두 기둥 + 바닥을 라운드 사각형 외곽선처럼 그림
    draw.line([(tray_left, tray_top), (tray_left, tray_bottom)], fill=WHITE, width=lw)
    draw.line([(tray_right, tray_top), (tray_right, tray_bottom)], fill=WHITE, width=lw)
    draw.line([(tray_left, tray_bottom), (tray_right, tray_bottom)], fill=WHITE, width=lw)
    # 모서리 둥글게
    r = lw // 2
    for px, py in [(tray_left, tray_bottom), (tray_right, tray_bottom)]:
        draw.ellipse([px - r, py - r, px + r, py + r], fill=WHITE)

    return img


def main():
    base = draw_icon(scale=1)
    base.save("icon.png")
    print("[icon] saved icon.png (1024x1024)")

    sizes = [16, 24, 32, 48, 64, 128, 256]
    base.save("icon.ico", sizes=[(n, n) for n in sizes])
    print(f"[icon] saved icon.ico ({', '.join(str(n) for n in sizes)})")


if __name__ == "__main__":
    main()
