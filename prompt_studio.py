#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt Studio — ComfyUI 프롬프트 생성기 (다크 테마)
==================================================
CustomTkinter 로 만든 모던 다크 UI. 생성/번역 로직은 comfy_prompt_generator
모듈을 재사용한다.

실행:  python prompt_studio.py
빌드:  pyinstaller 로 단일 .exe 패키징 (README / GitHub Actions 참고)
"""

from __future__ import annotations

import customtkinter as ctk
from tkinter import filedialog

import comfy_prompt_generator as engine

# ---------------------------------------------------------------------------
# 추가 옵션 표 (라벨, 영어 태그) — UI 전용
# ---------------------------------------------------------------------------
FRAMINGS = [
    ("지정 안 함", ""),
    ("중앙 구도", "centered composition"),
    ("삼분할 구도", "rule of thirds"),
    ("대칭 구도", "symmetrical composition"),
    ("타이트 프레이밍", "tight framing"),
    ("여백 많은", "negative space, minimalist composition"),
]
LIGHTINGS = [
    ("지정 안 함", ""),
    ("소프트라이트", "soft lighting"),
    ("시네마틱", "cinematic lighting"),
    ("림라이트", "rim lighting"),
    ("역광", "backlight"),
    ("네온", "neon lighting"),
    ("스튜디오", "studio lighting"),
    ("자연광", "natural lighting"),
    ("드라마틱", "dramatic lighting"),
]
TIMES = [
    ("지정 안 함", ""),
    ("골든아워", "golden hour"),
    ("한낮", "midday sun"),
    ("황혼", "dusk"),
    ("밤", "night"),
    ("새벽", "dawn"),
    ("흐림", "overcast"),
    ("비", "rainy atmosphere"),
]
MOODS = [
    ("지정 안 함", ""),
    ("평화로운", "peaceful mood"),
    ("긴장감", "tense atmosphere"),
    ("몽환적", "dreamy atmosphere"),
    ("음울한", "gloomy mood"),
    ("활기찬", "energetic mood"),
    ("로맨틱", "romantic mood"),
    ("미스터리", "mysterious mood"),
    ("웅장한", "epic atmosphere"),
]

PURPLE = "#6c5ce7"
PURPLE_HOVER = "#5a4fcf"
MAX_CHARS = 1500

# 자세(포즈) 30종 — 의미가 겹치지 않게 선별. (라벨, 영어 태그)
POSES_30 = [
    ("서기", "standing"),
    ("앉기", "sitting"),
    ("무릎꿇기", "kneeling"),
    ("쪼그려앉기", "squatting"),
    ("걷기", "walking"),
    ("달리기", "running"),
    ("점프", "jumping"),
    ("눕기", "lying down"),
    ("엎드리기", "lying on stomach"),
    ("기대기", "leaning against wall"),
    ("팔짱", "crossed arms"),
    ("허리에손", "hands on hips"),
    ("손흔들기", "waving"),
    ("손뻗기", "reaching out"),
    ("가리키기", "pointing"),
    ("만세", "arms raised"),
    ("뒤돌아보기", "looking back"),
    ("옆보기", "looking to the side"),
    ("위보기", "looking up"),
    ("아래보기", "looking down"),
    ("춤추기", "dancing"),
    ("전투자세", "fighting stance"),
    ("달려들기", "lunging forward"),
    ("발차기", "kicking"),
    ("스트레칭", "stretching"),
    ("웅크리기", "crouching"),
    ("기지개", "arching back"),
    ("무기들기", "holding a weapon"),
    ("머리만지기", "hand in own hair"),
    ("턱괴기", "hand on chin"),
]


def _rows(rows3):
    """(라벨, 슬러그, 태그) 3-튜플 표 → [(라벨, 태그)]."""
    return [(r[0], r[2]) for r in rows3]


SHOTS = _rows(engine.SHOT_SIZES)
ANGLES = _rows(engine.CAMERA_ANGLES)
EXPRS = _rows(engine.EXPRESSIONS)
COUNTS = [(label, key) for label, key, _ in engine.COUNTS]


class Section(ctk.CTkFrame):
    """접이식 섹션 (헤더 클릭 시 본문 토글)."""

    def __init__(self, master, title, opened=True):
        super().__init__(master, fg_color="transparent")
        self.title = title
        self.opened = opened
        self.header = ctk.CTkButton(
            self, text=self._htext(), anchor="w", height=30,
            fg_color="transparent", hover_color="#2a2a35",
            text_color="#dddde5", font=ctk.CTkFont(size=13, weight="bold"),
            command=self.toggle)
        self.header.pack(fill="x")
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        if opened:
            self.body.pack(fill="x", padx=10, pady=(2, 4))
        self.body.columnconfigure(1, weight=1)
        self._r = 0

    def _htext(self):
        return f"{'⌄' if self.opened else '›'}  {self.title}"

    def toggle(self):
        self.opened = not self.opened
        self.header.configure(text=self._htext())
        if self.opened:
            self.body.pack(fill="x", padx=10, pady=(2, 4))
        else:
            self.body.pack_forget()

    # --- 본문에 위젯 추가 헬퍼 ---
    def add_entry(self, label, placeholder=""):
        ctk.CTkLabel(self.body, text=label, width=58, anchor="w").grid(
            row=self._r, column=0, sticky="w", pady=3)
        var = ctk.StringVar()
        ent = ctk.CTkEntry(self.body, textvariable=var, placeholder_text=placeholder)
        ent.grid(row=self._r, column=1, sticky="ew", pady=3)
        self._r += 1
        return var, ent

    def add_menu(self, label, rows):
        ctk.CTkLabel(self.body, text=label, width=58, anchor="w").grid(
            row=self._r, column=0, sticky="w", pady=3)
        values = [r[0] for r in rows]
        menu = ctk.CTkOptionMenu(self.body, values=values, fg_color="#2a2a35",
                                 button_color="#3a3a48", dropdown_fg_color="#2a2a35")
        menu.set(values[0])
        menu.grid(row=self._r, column=1, sticky="ew", pady=3)
        self._r += 1
        return menu, {r[0]: r[1] for r in rows}


class PromptStudio(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title("Prompt Studio")
        self.geometry("1280x820")
        self.minsize(1080, 680)
        self.configure(fg_color="#16161e")
        self._tcache: dict = {}
        self._seed = None

        self._build_header()
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._build_left(body)
        self._build_right(body)
        # 시작 시 자동 생성하지 않는다 — 설정 후 Generate 를 눌러야 나온다.
        self.status.configure(text="설정을 마친 뒤 ✦ Generate 를 누르세요")

    # ---------------- Header ----------------
    def _build_header(self):
        bar = ctk.CTkFrame(self, fg_color="transparent", height=48)
        bar.pack(fill="x", padx=14, pady=(8, 4))
        logo = ctk.CTkLabel(bar, text=" P ", fg_color=PURPLE, corner_radius=6,
                            font=ctk.CTkFont(size=15, weight="bold"))
        logo.pack(side="left")
        ctk.CTkLabel(bar, text="Prompt Studio",
                     font=ctk.CTkFont(size=17, weight="bold")).pack(
            side="left", padx=(8, 16))
        proj = ctk.CTkOptionMenu(bar, values=["새 프로젝트"], width=130,
                                 fg_color="#2a2a35", button_color="#3a3a48")
        proj.pack(side="left")
        for txt, cmd in (("⚙", self.toggle_mode), ("💾", self.save_prompts),
                         ("📁", self.load_prompts)):
            ctk.CTkButton(bar, text=txt, width=36, fg_color="#2a2a35",
                          hover_color="#3a3a48", command=cmd).pack(
                side="right", padx=3)

    # ---------------- Left (settings) ----------------
    def _build_left(self, parent):
        wrap = ctk.CTkFrame(parent, fg_color="#1c1c26", corner_radius=10,
                            width=380)
        wrap.pack(side="left", fill="y", padx=(0, 10))
        wrap.pack_propagate(False)

        top = ctk.CTkFrame(wrap, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(12, 4))
        ctk.CTkLabel(top, text="설정",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="⇄ 템플릿", width=80, fg_color="#2a2a35",
                      hover_color="#3a3a48", command=self.apply_template).pack(
            side="right")

        scroll = ctk.CTkScrollableFrame(wrap, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        # 스타일
        s = Section(scroll, "스타일")
        s.pack(fill="x")
        ctk.CTkLabel(s.body, text="스타일", width=58, anchor="w").grid(
            row=0, column=0, sticky="w", pady=3)
        self.style_labels = [f"{v['label']}" for v in engine.STYLES.values()]
        self.style_keys = list(engine.STYLES.keys())
        self.style_menu = ctk.CTkOptionMenu(
            s.body, values=self.style_labels,
            fg_color="#2a2a35", button_color="#3a3a48")
        self.style_menu.grid(row=0, column=1, sticky="ew", pady=3)
        chk = ctk.CTkFrame(s.body, fg_color="transparent")
        chk.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.gray_var = ctk.BooleanVar()
        self.bw_var = ctk.BooleanVar()
        self.emph_var = ctk.BooleanVar(value=True)
        for t, v in (("무채색", self.gray_var), ("흑백", self.bw_var),
                     ("시점/샷 강조", self.emph_var)):
            ctk.CTkCheckBox(chk, text=t, variable=v,
                            checkbox_width=18, checkbox_height=18).pack(
                side="left", padx=(0, 10))

        # 인물
        s = Section(scroll, "인물")
        s.pack(fill="x")
        self.person_var, _ = s.add_entry("인물:")
        self.gender_var, _ = s.add_entry("성별:")
        self.age_var, _ = s.add_entry("연령:")
        self.trait_var, _ = s.add_entry("특징:")

        # 배경
        s = Section(scroll, "배경")
        s.pack(fill="x")
        self.place_var, _ = s.add_entry("장소:")
        self.bgdesc_var, _ = s.add_entry("배경 설명:")

        # 구도 / 카메라
        s = Section(scroll, "구도 / 카메라")
        s.pack(fill="x")
        self.shot_menu, self.shot_map = s.add_menu("샷", SHOTS)
        self.angle_menu, self.angle_map = s.add_menu("앵글", ANGLES)
        self.frame_menu, self.frame_map = s.add_menu("프레이밍", FRAMINGS)

        # 조명
        s = Section(scroll, "조명")
        s.pack(fill="x")
        self.light_menu, self.light_map = s.add_menu("조명", LIGHTINGS)
        self.time_menu, self.time_map = s.add_menu("시간 / 분위기", TIMES)

        # 감정 / 분위기
        s = Section(scroll, "감정 / 분위기")
        s.pack(fill="x")
        self.emo_menu, self.emo_map = s.add_menu("감정", EXPRS)
        self.mood_menu, self.mood_map = s.add_menu("분위기", MOODS)

        # 자세 / 포즈 (다중 선택, 30종 / 3열)
        s = Section(scroll, "자세 / 포즈")
        s.pack(fill="x")
        pose_box = ctk.CTkFrame(s.body, fg_color="transparent")
        pose_box.grid(row=0, column=0, columnspan=2, sticky="w")
        POSE_COLS = 3
        self.pose_vars: dict[str, ctk.BooleanVar] = {}
        for idx, (label, tag) in enumerate(POSES_30):
            var = ctk.BooleanVar()
            self.pose_vars[tag] = var
            ctk.CTkCheckBox(pose_box, text=label, variable=var, width=104,
                            checkbox_width=18, checkbox_height=18,
                            font=ctk.CTkFont(size=12)).grid(
                row=idx // POSE_COLS, column=idx % POSE_COLS,
                sticky="w", padx=2, pady=3)

        # 의상 / 소품
        s = Section(scroll, "의상 / 소품")
        s.pack(fill="x")
        self.cloth_var, _ = s.add_entry("의상:", "의상 설명을 입력하세요")
        self.prop_var, _ = s.add_entry("소품:", "소품 설명을 입력하세요")

        # 기타 옵션
        s = Section(scroll, "기타 옵션", opened=False)
        s.pack(fill="x")
        ctk.CTkLabel(s.body, text="인원수", width=58, anchor="w").grid(
            row=0, column=0, sticky="w", pady=3)
        self.count_menu = ctk.CTkOptionMenu(
            s.body, values=[c[0] for c in COUNTS],
            fg_color="#2a2a35", button_color="#3a3a48")
        self.count_menu.grid(row=0, column=1, sticky="ew", pady=3)
        self.count_map = {c[0]: c[1] for c in COUNTS}
        self.main_var, _ = s.add_entry("주인공:")
        opts = ctk.CTkFrame(s.body, fg_color="transparent")
        opts.grid(row=s._r, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.mainfocus_var = ctk.BooleanVar(value=True)
        self.random_var = ctk.BooleanVar(value=True)
        self.translate_var = ctk.BooleanVar(value=True)
        for t, v in (("주인공 강조", self.mainfocus_var),
                     ("무작위", self.random_var), ("한글번역", self.translate_var)):
            ctk.CTkCheckBox(opts, text=t, variable=v,
                            checkbox_width=18, checkbox_height=18).pack(
                side="left", padx=(0, 10))
        # 옵션 변경은 자동 생성하지 않는다 — Generate 버튼을 눌러야 반영됨.

    # ---------------- Right (output) ----------------
    def _build_right(self, parent):
        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        # Positive
        head = ctk.CTkFrame(right, fg_color="transparent")
        head.pack(fill="x")
        ctk.CTkLabel(head, text="Prompt",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        ctk.CTkButton(head, text="⧉ 복사", width=70, fg_color="#2a2a35",
                      hover_color="#3a3a48",
                      command=lambda: self.copy(self.pos_box)).pack(side="right")
        ctk.CTkButton(head, text="🗑 지우기", width=80, fg_color="#2a2a35",
                      hover_color="#3a3a48",
                      command=lambda: self.clear_box(self.pos_box)).pack(
            side="right", padx=6)
        self.pos_box = ctk.CTkTextbox(right, fg_color="#1c1c26",
                                      corner_radius=10, wrap="word")
        self.pos_box.pack(fill="both", expand=True, pady=(6, 0))
        self.pos_count = ctk.CTkLabel(right, text="0/1500", text_color="#888",
                                      anchor="w")
        self.pos_count.pack(fill="x", pady=(2, 8))

        # Negative
        head2 = ctk.CTkFrame(right, fg_color="transparent")
        head2.pack(fill="x")
        ctk.CTkLabel(head2, text="Negative Prompt",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        ctk.CTkButton(head2, text="⧉ 복사", width=70, fg_color="#2a2a35",
                      hover_color="#3a3a48",
                      command=lambda: self.copy(self.neg_box)).pack(side="right")
        ctk.CTkButton(head2, text="🗑 지우기", width=80, fg_color="#2a2a35",
                      hover_color="#3a3a48",
                      command=lambda: self.clear_box(self.neg_box)).pack(
            side="right", padx=6)
        self.neg_box = ctk.CTkTextbox(right, fg_color="#1c1c26",
                                      corner_radius=10, wrap="word")
        self.neg_box.pack(fill="both", expand=True, pady=(6, 0))
        self.neg_count = ctk.CTkLabel(right, text="0/1500", text_color="#888",
                                      anchor="w")
        self.neg_count.pack(fill="x", pady=(2, 8))

        for box, lbl in ((self.pos_box, self.pos_count),
                         (self.neg_box, self.neg_count)):
            box.bind("<KeyRelease>", lambda e, b=box, l=lbl: self._count(b, l))

        # 하단 버튼
        bottom = ctk.CTkFrame(right, fg_color="transparent")
        bottom.pack(fill="x")
        ctk.CTkButton(bottom, text="↻ 초기화", width=110, fg_color="#2a2a35",
                      hover_color="#3a3a48", command=self.reset).pack(side="left")
        self.status = ctk.CTkLabel(bottom, text="", text_color="#4caf80")
        self.status.pack(side="left", padx=12)
        ctk.CTkButton(bottom, text="✦  Generate", width=150, height=40,
                      fg_color=PURPLE, hover_color=PURPLE_HOVER,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=lambda: self.generate(new_seed=True)).pack(
            side="right")

    # ---------------- Logic ----------------
    def _tr(self, text):
        if not self.translate_var.get():
            return text
        out, _ = engine.translate_text(text, online=True, cache=self._tcache)
        return out

    def _join(self, *vals):
        parts = []
        for v in vals:
            v = (v or "").strip()
            if v:
                parts.append(self._tr(v))
        return ", ".join(parts)

    def generate(self, new_seed=False):
        import random
        if new_seed or self._seed is None:
            self._seed = random.randrange(1_000_000_000)
        style = self.style_keys[self.style_labels.index(self.style_menu.get())]
        character = self._join(self.person_var.get(), self.gender_var.get(),
                               self.age_var.get(), self.trait_var.get(),
                               self.cloth_var.get(), self.prop_var.get())
        background = self._join(self.place_var.get(), self.bgdesc_var.get())
        situation = self._join(self.main_get_mood())
        main_subject = self._tr(self.main_var.get().strip()) or None

        extra = [self.frame_map[self.frame_menu.get()],
                 self.light_map[self.light_menu.get()],
                 self.time_map[self.time_menu.get()]]
        if self.gray_var.get():
            extra.append("desaturated, muted colors")
        if self.bw_var.get():
            extra.append("monochrome, black and white, grayscale")

        count = self.count_map[self.count_menu.get()]
        poses = [tag for tag, v in self.pose_vars.items() if v.get()]
        result = engine.generate(
            style, character=character or None, background=background or None,
            situation=situation or None, randomize=self.random_var.get(),
            seed=self._seed, shot=self.shot_map[self.shot_menu.get()],
            angle=self.angle_map[self.angle_menu.get()],
            expression=self.emo_map[self.emo_menu.get()], poses=poses,
            count=count, main_subject=main_subject,
            main_focus=self.mainfocus_var.get(), emphasis=self.emph_var.get(),
            extra_tags=extra,
        )
        self._set(self.pos_box, result["positive"], self.pos_count)
        self._set(self.neg_box, result["negative"], self.neg_count)
        self.status.configure(text="✓ 생성됨")

    def main_get_mood(self):
        return self.mood_map[self.mood_menu.get()]

    # ---------------- Textbox helpers ----------------
    def _set(self, box, text, count_lbl):
        box.delete("1.0", "end")
        box.insert("1.0", text)
        self._count(box, count_lbl)

    def _count(self, box, count_lbl):
        n = len(box.get("1.0", "end-1c"))
        count_lbl.configure(text=f"{n}/{MAX_CHARS}",
                            text_color="#e06c6c" if n > MAX_CHARS else "#888")

    def copy(self, box):
        self.clipboard_clear()
        self.clipboard_append(box.get("1.0", "end-1c").strip())
        self.status.configure(text="✓ 복사됨")

    def clear_box(self, box):
        box.delete("1.0", "end")
        self._count(box, self.pos_count if box is self.pos_box else self.neg_count)

    def reset(self):
        for var in (self.person_var, self.gender_var, self.age_var,
                    self.trait_var, self.place_var, self.bgdesc_var,
                    self.cloth_var, self.prop_var, self.main_var):
            var.set("")
        for menu in (self.shot_menu, self.angle_menu, self.frame_menu,
                     self.light_menu, self.time_menu, self.emo_menu,
                     self.mood_menu):
            menu.set(menu.cget("values")[0])
        self.gray_var.set(False)
        self.bw_var.set(False)
        for v in self.pose_vars.values():
            v.set(False)
        self.count_menu.set(COUNTS[0][0])
        self.generate(new_seed=True)

    def apply_template(self):
        """간단한 인물 포트레이트 템플릿 채우기."""
        self.style_menu.set(self.style_labels[0])
        self.person_var.set("woman")
        self.trait_var.set("detailed face")
        self.shot_menu.set(SHOTS[3][0])     # 포트레이트
        self.light_menu.set(LIGHTINGS[2][0])  # 시네마틱
        self.time_menu.set(TIMES[1][0])       # 골든아워
        self.generate(new_seed=True)

    def toggle_mode(self):
        mode = "light" if ctk.get_appearance_mode() == "Dark" else "dark"
        ctk.set_appearance_mode(mode)

    def save_prompts(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("[Positive]\n" + self.pos_box.get("1.0", "end-1c").strip())
            f.write("\n\n[Negative]\n" + self.neg_box.get("1.0", "end-1c").strip())
        self.status.configure(text="✓ 저장됨")

    def load_prompts(self):
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
        if not path:
            return
        with open(path, encoding="utf-8") as f:
            text = f.read()
        self._set(self.pos_box, text, self.pos_count)
        self.status.configure(text="✓ 불러옴")


def main():
    app = PromptStudio()
    app.mainloop()


if __name__ == "__main__":
    main()
