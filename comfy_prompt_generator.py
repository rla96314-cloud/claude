#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComfyUI Prompt Generator
========================
ComfyUI / Stable Diffusion 용 긍정문(positive) · 부정문(negative) 프롬프트 생성기.

- 추가 설치 필요 없음 (파이썬 표준 라이브러리만 사용, GUI 는 tkinter)
- GUI 모드:  python comfy_prompt_generator.py
- CLI 모드:  python comfy_prompt_generator.py --cli ...

지원 스타일: realistic(실사) / anime(애니) / fantasy(판타지/컨셉아트)

CLI 예시
--------
  # 실사 인물 프롬프트 1개 생성
  python comfy_prompt_generator.py --cli --style realistic --subject "1girl, long hair"

  # 애니 스타일 랜덤 5개
  python comfy_prompt_generator.py --cli --style anime --random -n 5

  # 사용 가능한 태그/스타일 목록 보기
  python comfy_prompt_generator.py --cli --list
"""

from __future__ import annotations

import argparse
import random
import sys
import textwrap

# ---------------------------------------------------------------------------
# 1. 태그 라이브러리 (스타일별)
# ---------------------------------------------------------------------------
# 각 스타일은 positive 프롬프트를 구성하는 카테고리별 후보 태그를 가진다.
# 'quality' 는 맨 앞에 붙는 품질 부스트 태그, 그 외는 랜덤/선택 대상.

STYLES = {
    "realistic": {
        "label": "실사 / 포토리얼리즘",
        "quality": [
            "masterpiece", "best quality", "ultra detailed", "8k uhd",
            "photorealistic", "RAW photo", "high resolution",
        ],
        "subject": [
            "1girl", "1boy", "portrait of a woman", "portrait of a man",
            "elderly fisherman", "young athlete", "businesswoman",
        ],
        "appearance": [
            "detailed skin texture", "freckles", "natural makeup",
            "wavy brown hair", "short black hair", "blue eyes",
            "athletic build", "elegant dress", "casual streetwear",
        ],
        "scene": [
            "in a cozy cafe", "on a city street at night", "in a sunlit forest",
            "on a beach at sunset", "in a modern studio", "in an old library",
        ],
        "lighting": [
            "soft natural lighting", "golden hour lighting", "rim lighting",
            "cinematic lighting", "studio softbox lighting", "dramatic shadows",
        ],
        "camera": [
            "shot on Canon EOS R5", "85mm f/1.4 lens", "shallow depth of field",
            "bokeh background", "sharp focus", "professional color grading",
        ],
    },
    "anime": {
        "label": "애니 / 일러스트",
        "quality": [
            "masterpiece", "best quality", "amazing quality", "very aesthetic",
            "highly detailed", "absurdres",
        ],
        "subject": [
            "1girl", "1boy", "2girls", "chibi character",
            "magical girl", "samurai warrior", "school student",
        ],
        "appearance": [
            "long flowing hair", "twin tails", "cat ears", "heterochromia",
            "school uniform", "kimono", "fantasy armor", "hoodie",
            "detailed eyes", "blush",
        ],
        "scene": [
            "cherry blossom background", "futuristic city", "classroom",
            "starry night sky", "floating islands", "rainy street",
        ],
        "lighting": [
            "soft lighting", "vibrant colors", "glowing particles",
            "sunset glow", "neon lights", "god rays",
        ],
        "camera": [
            "dynamic angle", "depth of field", "cowboy shot",
            "upper body", "wide shot", "detailed background",
        ],
    },
    "fantasy": {
        "label": "판타지 / 컨셉아트",
        "quality": [
            "masterpiece", "best quality", "concept art", "highly detailed",
            "trending on artstation", "cinematic", "intricate details",
        ],
        "subject": [
            "ancient dragon", "elven ranger", "dwarven blacksmith",
            "floating sky castle", "enchanted forest", "cyberpunk mercenary",
            "celestial goddess",
        ],
        "appearance": [
            "ornate armor", "glowing runes", "flowing robes",
            "battle-worn cloak", "bioluminescent details", "crystal weapon",
            "intricate tattoos",
        ],
        "scene": [
            "epic mountain landscape", "ruined temple", "underground cavern",
            "alien planet", "stormy ocean", "neon-lit megacity",
        ],
        "lighting": [
            "volumetric lighting", "dramatic atmosphere", "ethereal glow",
            "moody fog", "backlit silhouette", "magical aura",
        ],
        "camera": [
            "epic wide shot", "low angle", "matte painting", "8k",
            "unreal engine render", "octane render",
        ],
    },
}

# ---------------------------------------------------------------------------
# 2. 부정문(negative) 프리셋
# ---------------------------------------------------------------------------
NEGATIVE_COMMON = [
    "lowres", "bad anatomy", "bad hands", "extra digits", "fewer digits",
    "cropped", "worst quality", "low quality", "jpeg artifacts",
    "signature", "watermark", "username", "blurry", "text", "error",
    "out of frame", "deformed", "mutated", "ugly", "duplicate",
]

NEGATIVE_BY_STYLE = {
    "realistic": [
        "cartoon", "anime", "illustration", "painting", "3d render",
        "plastic skin", "overexposed", "extra limbs", "disfigured face",
    ],
    "anime": [
        "extra fingers", "fused fingers", "long neck", "bad proportions",
        "poorly drawn face", "poorly drawn hands", "missing limb",
        "extra arms", "extra legs", "censored",
    ],
    "fantasy": [
        "flat lighting", "boring composition", "low detail",
        "amateur", "bad perspective", "oversaturated", "noise",
    ],
}


# ---------------------------------------------------------------------------
# 3. 프롬프트 빌드 로직
# ---------------------------------------------------------------------------
def build_positive(style: str, subject: str | None = None,
                   randomize: bool = True, seed: int | None = None) -> str:
    """긍정문(positive) 프롬프트를 만든다.

    style     : STYLES 키 (realistic / anime / fantasy)
    subject   : 사용자가 직접 지정한 주제. 없으면 라이브러리에서 선택.
    randomize : True 면 각 카테고리에서 무작위로 뽑고, False 면 앞쪽 태그 사용.
    seed      : 재현 가능한 랜덤을 위한 시드.
    """
    if style not in STYLES:
        raise ValueError(f"알 수 없는 스타일: {style!r} (가능: {', '.join(STYLES)})")

    rng = random.Random(seed)
    data = STYLES[style]

    def pick(category: str, k: int = 1) -> list[str]:
        pool = data[category]
        if randomize:
            return rng.sample(pool, min(k, len(pool)))
        return pool[:k]

    parts: list[str] = []
    # 품질 태그 (2~3개)
    parts += pick("quality", 3 if randomize else 2)
    # 주제
    if subject:
        parts.append(subject.strip())
    else:
        parts += pick("subject", 1)
    # 외형 / 장면 / 조명 / 카메라
    parts += pick("appearance", 2)
    parts += pick("scene", 1)
    parts += pick("lighting", 1)
    parts += pick("camera", 1)

    # 중복 제거 (순서 유지)
    seen: set[str] = set()
    unique = [p for p in parts if not (p in seen or seen.add(p))]
    return ", ".join(unique)


def build_negative(style: str) -> str:
    """부정문(negative) 프롬프트를 만든다."""
    tags = list(NEGATIVE_COMMON) + NEGATIVE_BY_STYLE.get(style, [])
    seen: set[str] = set()
    unique = [t for t in tags if not (t in seen or seen.add(t))]
    return ", ".join(unique)


def generate(style: str, subject: str | None = None,
            randomize: bool = True, seed: int | None = None) -> dict:
    """positive / negative 를 함께 반환."""
    return {
        "style": style,
        "positive": build_positive(style, subject, randomize, seed),
        "negative": build_negative(style),
    }


# ---------------------------------------------------------------------------
# 4. CLI
# ---------------------------------------------------------------------------
def run_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="comfy_prompt_generator --cli",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="ComfyUI 용 긍정/부정 프롬프트 생성 (CLI)",
    )
    parser.add_argument("--cli", action="store_true", help="CLI 모드로 실행")
    parser.add_argument("--style", choices=list(STYLES), default="realistic",
                        help="그림 스타일 (기본: realistic)")
    parser.add_argument("--subject", default=None,
                        help="직접 지정할 주제 (예: '1girl, long hair')")
    parser.add_argument("--random", dest="randomize", action="store_true",
                        default=True, help="카테고리별 무작위 선택 (기본 활성)")
    parser.add_argument("--no-random", dest="randomize", action="store_false",
                        help="무작위 대신 대표 태그 사용")
    parser.add_argument("-n", "--count", type=int, default=1,
                        help="생성할 프롬프트 개수 (기본 1)")
    parser.add_argument("--seed", type=int, default=None, help="랜덤 시드")
    parser.add_argument("--list", action="store_true",
                        help="스타일/태그 목록 출력 후 종료")
    args = parser.parse_args(argv)

    if args.list:
        for key, data in STYLES.items():
            print(f"\n■ {key}  ({data['label']})")
            for cat, tags in data.items():
                if cat == "label":
                    continue
                print(f"   - {cat:11s}: {', '.join(tags)}")
        return 0

    for i in range(max(1, args.count)):
        seed = args.seed if args.seed is None else args.seed + i
        result = generate(args.style, args.subject, args.randomize, seed)
        header = f" 프롬프트 #{i + 1} [{args.style}] "
        print("\n" + header.center(60, "="))
        print("\n[ Positive ]")
        print(textwrap.fill(result["positive"], width=72,
                            subsequent_indent="  "))
        print("\n[ Negative ]")
        print(textwrap.fill(result["negative"], width=72,
                            subsequent_indent="  "))
    print()
    return 0


# ---------------------------------------------------------------------------
# 5. GUI (tkinter)
# ---------------------------------------------------------------------------
def run_gui() -> int:
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except Exception as exc:  # pragma: no cover - 환경에 tkinter 없을 때
        print("tkinter 를 불러올 수 없습니다. CLI 모드를 사용하세요:")
        print("  python comfy_prompt_generator.py --cli --help")
        print(f"(원인: {exc})")
        return 1

    root = tk.Tk()
    root.title("ComfyUI 프롬프트 생성기")
    root.geometry("760x620")
    root.minsize(640, 540)

    main = ttk.Frame(root, padding=12)
    main.pack(fill="both", expand=True)

    # --- 상단 컨트롤 ---
    ctrl = ttk.Frame(main)
    ctrl.pack(fill="x", pady=(0, 8))

    ttk.Label(ctrl, text="스타일:").grid(row=0, column=0, sticky="w", padx=(0, 4))
    style_var = tk.StringVar(value="realistic")
    style_labels = {k: f"{k} ({v['label']})" for k, v in STYLES.items()}
    style_combo = ttk.Combobox(
        ctrl, state="readonly", width=24,
        values=list(style_labels.values()),
    )
    style_combo.current(0)
    style_combo.grid(row=0, column=1, sticky="w", padx=(0, 12))

    randomize_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(ctrl, text="무작위", variable=randomize_var).grid(
        row=0, column=2, sticky="w", padx=(0, 12))

    ttk.Label(ctrl, text="주제(선택):").grid(row=1, column=0, sticky="w",
                                          padx=(0, 4), pady=(8, 0))
    subject_var = tk.StringVar()
    subject_entry = ttk.Entry(ctrl, textvariable=subject_var, width=46)
    subject_entry.grid(row=1, column=1, columnspan=2, sticky="we", pady=(8, 0))
    ctrl.columnconfigure(1, weight=1)

    def current_style_key() -> str:
        idx = style_combo.current()
        return list(STYLES.keys())[idx if idx >= 0 else 0]

    # --- 출력 영역 ---
    out_frame = ttk.Frame(main)
    out_frame.pack(fill="both", expand=True)

    ttk.Label(out_frame, text="Positive (긍정문)",
              font=("", 10, "bold")).pack(anchor="w")
    pos_text = tk.Text(out_frame, height=8, wrap="word")
    pos_text.pack(fill="both", expand=True, pady=(2, 8))

    ttk.Label(out_frame, text="Negative (부정문)",
              font=("", 10, "bold")).pack(anchor="w")
    neg_text = tk.Text(out_frame, height=8, wrap="word")
    neg_text.pack(fill="both", expand=True, pady=(2, 0))

    def set_text(widget, value: str) -> None:
        widget.delete("1.0", "end")
        widget.insert("1.0", value)

    def do_generate() -> None:
        style = current_style_key()
        subject = subject_var.get().strip() or None
        result = generate(style, subject, randomize_var.get())
        set_text(pos_text, result["positive"])
        set_text(neg_text, result["negative"])

    def copy_to_clipboard(widget) -> None:
        root.clipboard_clear()
        root.clipboard_append(widget.get("1.0", "end").strip())
        messagebox.showinfo("복사됨", "클립보드에 복사했습니다.")

    # --- 버튼 ---
    btns = ttk.Frame(main)
    btns.pack(fill="x", pady=(10, 0))
    ttk.Button(btns, text="🎲 생성", command=do_generate).pack(side="left")
    ttk.Button(btns, text="Positive 복사",
               command=lambda: copy_to_clipboard(pos_text)).pack(side="left", padx=6)
    ttk.Button(btns, text="Negative 복사",
               command=lambda: copy_to_clipboard(neg_text)).pack(side="left")
    ttk.Button(btns, text="닫기", command=root.destroy).pack(side="right")

    do_generate()  # 시작 시 한 번 채워두기
    root.mainloop()
    return 0


# ---------------------------------------------------------------------------
# 6. 엔트리 포인트
# ---------------------------------------------------------------------------
def main() -> int:
    argv = sys.argv[1:]
    if "--cli" in argv or "--list" in argv:
        return run_cli(argv)
    if argv:  # 알 수 없는 인자가 들어오면 CLI 도움말 쪽으로
        return run_cli(argv)
    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
