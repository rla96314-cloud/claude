#!/usr/bin/env python3
"""로컬 한↔영 번역기 (Ollama 기반 데스크톱 GUI)

Ollama가 로컬에서 제공하는 LLM을 사용해 한국어와 영어를 번역하는
Tkinter 데스크톱 애플리케이션입니다. 인터넷 없이 동작하며, 번역 요청은
http://localhost:11434 의 Ollama 서버로만 전송됩니다.

사용 전 준비:
    1. https://ollama.com 에서 Ollama 설치 후 실행
    2. 모델 하나 받기 (예: ollama pull qwen2.5:7b)
    3. python3 translator.py
"""

import json
import threading
import tkinter as tk
import urllib.error
import urllib.request
from tkinter import messagebox, ttk

OLLAMA_HOST = "http://localhost:11434"
REQUEST_TIMEOUT = 120  # 초

# 번역 방향 정의: 라벨 -> (출발어, 도착어)
DIRECTIONS = {
    "한국어 → English": ("한국어", "영어"),
    "English → 한국어": ("영어", "한국어"),
    "자동 감지": (None, None),
}

# 모델 목록을 못 가져왔을 때 보여줄 후보들
FALLBACK_MODELS = ["qwen2.5:7b", "gemma2:9b", "llama3.1:8b"]


def build_prompt(text: str, src: str, dst: str) -> str:
    """번역 지시 프롬프트를 구성한다."""
    if src is None or dst is None:
        # 자동 감지: 입력이 한국어면 영어로, 아니면 한국어로 번역하도록 지시
        return (
            "You are a professional Korean-English translator.\n"
            "Detect the language of the text below. "
            "If it is Korean, translate it into natural English. "
            "If it is English, translate it into natural Korean.\n"
            "Output ONLY the translation, with no explanations, no quotes, "
            "and no extra commentary.\n\n"
            f"Text:\n{text}"
        )
    return (
        f"You are a professional translator. Translate the following {src} text "
        f"into natural, fluent {dst}.\n"
        "Output ONLY the translation, with no explanations, no quotes, "
        "and no extra commentary.\n\n"
        f"{src} text:\n{text}"
    )


def fetch_models() -> list[str]:
    """Ollama에 설치된 모델 목록을 가져온다. 실패하면 빈 리스트."""
    try:
        req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        models = [m["name"] for m in data.get("models", [])]
        return models
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError):
        return []


def translate(text: str, model: str, src: str, dst: str) -> str:
    """Ollama /api/generate 를 호출해 번역 결과 문자열을 반환한다."""
    prompt = build_prompt(text, src, dst)
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result.get("response", "").strip()


class TranslatorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("로컬 한↔영 번역기 (Ollama)")
        root.geometry("760x560")
        root.minsize(560, 440)

        self._build_widgets()
        self._refresh_models()

    def _build_widgets(self) -> None:
        pad = {"padx": 10, "pady": 6}

        # 상단 컨트롤 줄
        top = ttk.Frame(self.root)
        top.pack(fill="x", **pad)

        ttk.Label(top, text="방향:").pack(side="left")
        self.direction = ttk.Combobox(
            top, values=list(DIRECTIONS.keys()), state="readonly", width=18
        )
        self.direction.current(0)
        self.direction.pack(side="left", padx=(4, 16))

        ttk.Label(top, text="모델:").pack(side="left")
        self.model = ttk.Combobox(top, state="readonly", width=22)
        self.model.pack(side="left", padx=4)

        ttk.Button(top, text="새로고침", command=self._refresh_models).pack(
            side="left", padx=4
        )

        # 입력
        ttk.Label(self.root, text="입력 텍스트:").pack(anchor="w", padx=10)
        self.input_text = tk.Text(self.root, height=8, wrap="word", font=("", 11))
        self.input_text.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        self.input_text.focus_set()

        # 가운데 버튼 줄
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

        # 출력
        ttk.Label(self.root, text="번역 결과:").pack(anchor="w", padx=10, pady=(6, 0))
        self.output_text = tk.Text(
            self.root, height=8, wrap="word", font=("", 11), state="disabled"
        )
        self.output_text.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        # 상태 표시줄
        self.status = tk.StringVar(value="준비됨")
        ttk.Label(self.root, textvariable=self.status, anchor="w").pack(
            fill="x", padx=10, pady=(0, 8)
        )

        # 단축키: Ctrl+Enter 로 번역
        self.root.bind("<Control-Return>", lambda _e: self.on_translate())

    def _refresh_models(self) -> None:
        self.status.set("모델 목록 불러오는 중…")
        self.root.update_idletasks()
        models = fetch_models()
        if models:
            self.model["values"] = models
            self.model.current(0)
            self.status.set(f"모델 {len(models)}개 발견")
        else:
            self.model["values"] = FALLBACK_MODELS
            self.model.current(0)
            self.status.set(
                "Ollama에 연결 못함 — Ollama 실행 여부와 'ollama pull'을 확인하세요"
            )

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
        text = self.input_text.get("1.0", "end").strip()
        if not text:
            self.status.set("번역할 텍스트를 입력하세요")
            return
        model = self.model.get().strip()
        if not model:
            messagebox.showwarning("모델 없음", "사용할 모델을 선택하세요.")
            return

        src, dst = DIRECTIONS[self.direction.get()]
        self.translate_btn.configure(state="disabled")
        self.status.set(f"'{model}' 모델로 번역 중…")

        # GUI가 멈추지 않도록 백그라운드 스레드에서 실행
        thread = threading.Thread(
            target=self._run_translation, args=(text, model, src, dst), daemon=True
        )
        thread.start()

    def _run_translation(self, text, model, src, dst) -> None:
        try:
            result = translate(text, model, src, dst)
            self.root.after(0, self._on_success, result)
        except urllib.error.URLError:
            self.root.after(
                0,
                self._on_error,
                "Ollama 서버에 연결할 수 없습니다.\n"
                "Ollama가 실행 중인지 (http://localhost:11434) 확인하세요.",
            )
        except Exception as exc:  # noqa: BLE001 - 사용자에게 메시지로 표시
            self.root.after(0, self._on_error, f"번역 중 오류가 발생했습니다:\n{exc}")

    def _on_success(self, result: str) -> None:
        self._set_output(result or "(빈 응답)")
        self.translate_btn.configure(state="normal")
        self.status.set("완료")

    def _on_error(self, message: str) -> None:
        self.translate_btn.configure(state="normal")
        self.status.set("오류")
        messagebox.showerror("오류", message)


def main() -> None:
    root = tk.Tk()
    TranslatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
