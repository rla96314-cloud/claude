#!/usr/bin/env python3
"""로컬 한↔영 번역기 (Hugging Face NLLB-200 기반 데스크톱 GUI)

Meta의 NLLB-200 번역 전용 모델을 로컬에서 직접 구동해 한국어 ↔ 영어를
번역합니다. Argos보다 품질이 높고, Ollama 같은 별도 서버가 필요 없습니다.

모델은 처음 한 번만 인터넷에서 내려받고(distilled-600M 기준 ~2.4GB),
그 뒤로는 완전히 오프라인으로 동작합니다.

사용 전 준비:
    pip install transformers torch sentencepiece
    python3 translator_nllb.py
"""

import re
import threading
import tkinter as tk
from tkinter import messagebox, ttk

# 단어 목록을 나눌 구분자: 쉼표, 줄바꿈, 가운뎃점, 슬래시, 세미콜론 등
TERM_SPLIT = re.compile(r"[,\n;/·•、]+")

# 모델 선택: 품질을 더 올리려면 "facebook/nllb-200-1.3B" (더 무거움/느림)
MODEL_NAME = "facebook/nllb-200-distilled-600M"

# NLLB 언어 코드
KO = "kor_Hang"
EN = "eng_Latn"

# 라벨 -> (src_code, tgt_code)
DIRECTIONS = {
    "한국어 → English": (KO, EN),
    "English → 한국어": (EN, KO),
}

# 빔서치 개수: 클수록 품질↑ 속도↓
NUM_BEAMS = 5
MAX_NEW_TOKENS = 512

# 모델/토크나이저는 처음 사용할 때 한 번만 로드 (지연 로딩)
_model = None
_tokenizer = None


def load_model(progress=None) -> None:
    """모델과 토크나이저를 메모리에 로드한다 (최초 1회, 무거움)."""
    global _model, _tokenizer
    if _model is not None:
        return
    if progress:
        progress("라이브러리 로딩 중…")
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    if progress:
        progress("토크나이저 로딩 중… (처음이면 모델 다운로드)")
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    if progress:
        progress("모델 로딩 중… (처음 한 번만 시간이 걸립니다)")
    _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)


def _generate(text: str, bos: int) -> str:
    """모델로 한 덩어리를 번역한다 (호출 전 src_lang 설정 필요)."""
    inputs = _tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    tokens = _model.generate(
        **inputs,
        forced_bos_token_id=bos,
        max_new_tokens=MAX_NEW_TOKENS,
        num_beams=NUM_BEAMS,
        no_repeat_ngram_size=3,
    )
    return _tokenizer.batch_decode(tokens, skip_special_tokens=True)[0]


def translate(text: str, src: str, tgt: str, progress=None) -> str:
    """줄 단위로 나눠 번역해 긴 글의 잘림을 줄이고 형식을 보존한다."""
    load_model(progress)
    _tokenizer.src_lang = src
    bos = _tokenizer.convert_tokens_to_ids(tgt)

    out_lines = []
    for line in text.split("\n"):
        if not line.strip():
            out_lines.append("")
            continue
        out_lines.append(_generate(line, bos))
    return "\n".join(out_lines)


def translate_terms(text: str, src: str, tgt: str, progress=None) -> str:
    """단어/표현을 하나씩 따로 번역한다.

    문장 번역기가 단어 목록을 한 문장으로 오해해 없는 주어·대명사를 끼워넣거나
    엉뚱하게 지칭하는 문제를 막기 위해, 각 항목을 독립적으로 번역하고
    `원어  →  번역` 형태로 정렬해 보여준다.
    """
    load_model(progress)
    _tokenizer.src_lang = src
    bos = _tokenizer.convert_tokens_to_ids(tgt)

    terms = [t.strip() for t in TERM_SPLIT.split(text) if t.strip()]
    out_lines = []
    for i, term in enumerate(terms, 1):
        if progress:
            progress(f"단어 번역 중… ({i}/{len(terms)})")
        out_lines.append(f"{term}  →  {_generate(term, bos)}")
    return "\n".join(out_lines)


class TranslatorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("로컬 한↔영 번역기 (NLLB-200)")
        root.geometry("760x560")
        root.minsize(560, 440)
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
        self.word_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            top,
            text="단어 목록 모드 (단어별 따로 번역)",
            variable=self.word_mode,
        ).pack(side="left", padx=(0, 16))

        ttk.Label(top, text=f"모델: {MODEL_NAME.split('/')[-1]}").pack(side="left")

        ttk.Label(
            self.root,
            text="입력 텍스트  (단어 목록 모드: 쉼표나 줄바꿈으로 단어를 구분하세요)",
        ).pack(anchor="w", padx=10)
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

    def _progress(self, msg: str) -> None:
        # 백그라운드 스레드에서 호출되므로 메인 스레드로 넘김
        self.root.after(0, self.status.set, msg)

    def on_translate(self) -> None:
        text = self.input_text.get("1.0", "end").strip()
        if not text:
            self.status.set("번역할 텍스트를 입력하세요")
            return
        src, tgt = DIRECTIONS[self.direction.get()]
        word_mode = self.word_mode.get()
        self.translate_btn.configure(state="disabled")
        self.status.set("번역 준비 중…")
        threading.Thread(
            target=self._run, args=(text, src, tgt, word_mode), daemon=True
        ).start()

    def _run(self, text, src, tgt, word_mode) -> None:
        try:
            fn = translate_terms if word_mode else translate
            result = fn(text, src, tgt, progress=self._progress)
            self.root.after(0, self._on_success, result)
        except ImportError:
            self.root.after(
                0,
                self._on_error,
                "필요한 라이브러리가 없습니다.\n"
                "터미널에서  pip install transformers torch sentencepiece  실행.",
            )
        except Exception as exc:  # noqa: BLE001 - 사용자에게 표시
            self.root.after(0, self._on_error, str(exc))

    def _on_success(self, result: str) -> None:
        self._set_output(result or "(빈 응답)")
        self.translate_btn.configure(state="normal")
        self.status.set("완료")

    def _on_error(self, message: str) -> None:
        self.translate_btn.configure(state="normal")
        self.status.set("오류")
        messagebox.showerror("오류", f"번역 중 오류가 발생했습니다:\n{message}")


def main() -> None:
    root = tk.Tk()
    TranslatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
