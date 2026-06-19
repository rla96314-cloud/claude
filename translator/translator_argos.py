#!/usr/bin/env python3
"""로컬 한↔영 번역기 (Argos Translate 기반 데스크톱 GUI)

Ollama 같은 별도 서버 없이, 파이썬 패키지(Argos Translate) 안에서 직접
한국어 ↔ 영어를 번역하는 Tkinter 데스크톱 앱입니다.

번역 모델은 처음 한 번만 인터넷에서 내려받고(각 ~100MB), 그 뒤로는
완전히 오프라인으로 동작합니다.

사용 전 준비:
    pip install argostranslate
    python3 translator_argos.py
"""

import threading
import tkinter as tk
from tkinter import messagebox, ttk

try:
    import argostranslate.package
    import argostranslate.translate
except ImportError:  # 친절한 안내를 위해 실행 시점에 다시 확인
    argostranslate = None

# 라벨 -> (from_code, to_code)
DIRECTIONS = {
    "한국어 → English": ("ko", "en"),
    "English → 한국어": ("en", "ko"),
}


def ensure_package(from_code: str, to_code: str) -> None:
    """해당 언어쌍 모델이 없으면 인터넷에서 내려받아 설치한다."""
    installed = argostranslate.translate.get_installed_languages()
    has = any(
        lang.code == from_code
        and any(t.to_lang.code == to_code for t in lang.translations_from)
        for lang in installed
    )
    if has:
        return

    # 패키지 인덱스 갱신 후 해당 언어쌍 다운로드/설치 (인터넷 필요, 1회성)
    argostranslate.package.update_package_index()
    available = argostranslate.package.get_available_packages()
    match = next(
        (p for p in available if p.from_code == from_code and p.to_code == to_code),
        None,
    )
    if match is None:
        raise RuntimeError(
            f"{from_code}->{to_code} 번역 모델을 찾을 수 없습니다."
        )
    argostranslate.package.install_from_path(match.download())


def translate(text: str, from_code: str, to_code: str) -> str:
    ensure_package(from_code, to_code)
    return argostranslate.translate.translate(text, from_code, to_code)


class TranslatorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("로컬 한↔영 번역기 (Argos)")
        root.geometry("760x540")
        root.minsize(560, 420)
        self._build_widgets()

    def _build_widgets(self) -> None:
        pad = {"padx": 10, "pady": 6}

        top = ttk.Frame(self.root)
        top.pack(fill="x", **pad)
        ttk.Label(top, text="방향:").pack(side="left")
        self.direction = ttk.Combobox(
            top, values=list(DIRECTIONS.keys()), state="readonly", width=18
        )
        self.direction.current(0)
        self.direction.pack(side="left", padx=(4, 16))

        ttk.Label(self.root, text="입력 텍스트:").pack(anchor="w", padx=10)
        self.input_text = tk.Text(self.root, height=8, wrap="word", font=("", 11))
        self.input_text.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        self.input_text.focus_set()

        mid = ttk.Frame(self.root)
        mid.pack(fill="x", padx=10)
        self.translate_btn = ttk.Button(
            mid, text="번역하기  (Ctrl+Enter)", command=self.on_translate
        )
        self.translate_btn.pack(side="left")
        ttk.Button(mid, text="입력 지우기", command=self._clear_input).pack(
            side="left", padx=6
        )
        ttk.Button(mid, text="결과 복사", command=self._copy_output).pack(side="left")

        ttk.Label(self.root, text="번역 결과:").pack(anchor="w", padx=10, pady=(6, 0))
        self.output_text = tk.Text(
            self.root, height=8, wrap="word", font=("", 11), state="disabled"
        )
        self.output_text.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        self.status = tk.StringVar(value="준비됨")
        ttk.Label(self.root, textvariable=self.status, anchor="w").pack(
            fill="x", padx=10, pady=(0, 8)
        )

        self.root.bind("<Control-Return>", lambda _e: self.on_translate())

    def _clear_input(self) -> None:
        self.input_text.delete("1.0", "end")
        self.input_text.focus_set()

    def _set_output(self, text: str) -> None:
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)
        self.output_text.configure(state="disabled")

    def _copy_output(self) -> None:
        text = self.output_text.get("1.0", "end").strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status.set("결과를 클립보드에 복사했습니다")

    def on_translate(self) -> None:
        if argostranslate is None:
            messagebox.showerror(
                "패키지 없음",
                "argostranslate 가 설치되어 있지 않습니다.\n"
                "터미널에서  pip install argostranslate  를 실행하세요.",
            )
            return
        text = self.input_text.get("1.0", "end").strip()
        if not text:
            self.status.set("번역할 텍스트를 입력하세요")
            return

        from_code, to_code = DIRECTIONS[self.direction.get()]
        self.translate_btn.configure(state="disabled")
        self.status.set("번역 중… (모델이 없으면 처음 한 번 내려받습니다)")
        threading.Thread(
            target=self._run, args=(text, from_code, to_code), daemon=True
        ).start()

    def _run(self, text, from_code, to_code) -> None:
        try:
            result = translate(text, from_code, to_code)
            self.root.after(0, self._on_success, result)
        except Exception as exc:  # noqa: BLE001 - 사용자에게 표시
            self.root.after(0, self._on_error, str(exc))

    def _on_success(self, result: str) -> None:
        self._set_output(result or "(빈 응답)")
        self.translate_btn.configure(state="normal")
        self.status.set("완료")

    def _on_error(self, message: str) -> None:
        self.translate_btn.configure(state="normal")
        self.status.set("오류")
        messagebox.showerror(
            "오류",
            f"번역 중 오류가 발생했습니다:\n{message}\n\n"
            "(모델 다운로드는 처음 한 번 인터넷이 필요합니다.)",
        )


def main() -> None:
    root = tk.Tk()
    TranslatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
