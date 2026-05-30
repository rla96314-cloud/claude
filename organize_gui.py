#!/usr/bin/env python3
"""파일 정리 프로그램 - GUI 버전 (File Organizer GUI)

클릭만으로 폴더 안의 파일을 종류별/날짜별로 자동 정리합니다.
파이썬 기본 내장 tkinter 만 사용하므로 추가 설치가 필요 없습니다.

실행:
    python organize_gui.py
"""

from __future__ import annotations

import threading
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import organize as core  # organize.py 의 핵심 로직 재사용


class OrganizerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("파일 정리 프로그램")
        root.geometry("640x520")
        root.minsize(560, 460)

        self.folder = tk.StringVar()
        self.by = tk.StringVar(value="type")
        self.recursive = tk.BooleanVar(value=False)
        self.last_plan: list[tuple[Path, Path]] = []

        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 6}

        # 1) 폴더 선택
        top = ttk.LabelFrame(self.root, text="1. 정리할 폴더")
        top.pack(fill="x", **pad)
        entry = ttk.Entry(top, textvariable=self.folder)
        entry.pack(side="left", fill="x", expand=True, padx=(10, 6), pady=10)
        ttk.Button(top, text="폴더 선택…", command=self.choose_folder).pack(
            side="left", padx=(0, 10), pady=10)

        # 2) 정리 기준
        opts = ttk.LabelFrame(self.root, text="2. 정리 방식")
        opts.pack(fill="x", **pad)
        ttk.Radiobutton(opts, text="종류별 (이미지·문서·동영상 …)",
                        variable=self.by, value="type").pack(anchor="w", padx=10, pady=(8, 0))
        ttk.Radiobutton(opts, text="날짜별 (수정 연-월 폴더)",
                        variable=self.by, value="date").pack(anchor="w", padx=10)
        ttk.Checkbutton(opts, text="하위 폴더의 파일까지 포함",
                        variable=self.recursive).pack(anchor="w", padx=10, pady=(0, 8))

        # 3) 실행 버튼
        actions = ttk.Frame(self.root)
        actions.pack(fill="x", **pad)
        self.btn_preview = ttk.Button(actions, text="👀 미리보기", command=self.on_preview)
        self.btn_preview.pack(side="left", padx=(10, 6))
        self.btn_apply = ttk.Button(actions, text="✅ 정리 실행", command=self.on_apply)
        self.btn_apply.pack(side="left", padx=6)
        self.btn_undo = ttk.Button(actions, text="↩️ 되돌리기", command=self.on_undo)
        self.btn_undo.pack(side="left", padx=6)

        # 4) 결과 로그
        logframe = ttk.LabelFrame(self.root, text="결과")
        logframe.pack(fill="both", expand=True, **pad)
        self.log = tk.Text(logframe, height=12, wrap="word", state="disabled",
                           background="#1e1e1e", foreground="#d4d4d4")
        self.log.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scroll = ttk.Scrollbar(logframe, command=self.log.yview)
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 6))
        self.log.configure(yscrollcommand=scroll.set)

        # 상태 표시줄
        self.status = tk.StringVar(value="폴더를 선택한 뒤 미리보기를 눌러 보세요.")
        ttk.Label(self.root, textvariable=self.status, relief="sunken",
                  anchor="w").pack(fill="x", side="bottom")

    # -------------------------------------------------------------- helpers
    def write_log(self, text: str, clear: bool = False) -> None:
        self.log.configure(state="normal")
        if clear:
            self.log.delete("1.0", "end")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def get_target(self) -> Path | None:
        path = self.folder.get().strip()
        if not path:
            messagebox.showwarning("폴더 없음", "먼저 정리할 폴더를 선택하세요.")
            return None
        target = Path(path).expanduser()
        if not target.is_dir():
            messagebox.showerror("오류", f"폴더를 찾을 수 없습니다:\n{target}")
            return None
        return target.resolve()

    def set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        for b in (self.btn_preview, self.btn_apply, self.btn_undo):
            b.configure(state=state)

    def choose_folder(self) -> None:
        chosen = filedialog.askdirectory(title="정리할 폴더 선택")
        if chosen:
            self.folder.set(chosen)
            self.status.set(f"선택됨: {chosen}")

    # --------------------------------------------------------------- actions
    def _summary(self, moves: list[tuple[Path, Path]]) -> str:
        grouped: dict[str, int] = {}
        for _, dest in moves:
            folder = dest.parent.name
            grouped[folder] = grouped.get(folder, 0) + 1
        lines = [f"총 {len(moves)}개 파일", ""]
        for folder in sorted(grouped):
            lines.append(f"  📁 {folder}/   {grouped[folder]}개")
        return "\n".join(lines)

    def on_preview(self) -> None:
        target = self.get_target()
        if not target:
            return
        moves = core.plan_moves(target, by=self.by.get(), recursive=self.recursive.get())
        self.last_plan = moves
        if not moves:
            self.write_log("정리할 파일이 없습니다.", clear=True)
            self.status.set("정리할 파일 없음")
            return
        self.write_log("[미리보기]\n" + self._summary(moves), clear=True)
        self.write_log("\n— 자세히 —")
        for src, dest in moves:
            self.write_log(f"  {src.name}  →  {dest.parent.name}/{dest.name}")
        self.status.set(f"{len(moves)}개 정리 예정 — '정리 실행'을 누르면 적용됩니다.")

    def on_apply(self) -> None:
        target = self.get_target()
        if not target:
            return
        moves = core.plan_moves(target, by=self.by.get(), recursive=self.recursive.get())
        if not moves:
            self.write_log("정리할 파일이 없습니다.", clear=True)
            self.status.set("정리할 파일 없음")
            return
        if not messagebox.askyesno("정리 실행",
                                   f"{len(moves)}개 파일을 정리할까요?\n"
                                   "(나중에 '되돌리기'로 복구할 수 있습니다.)"):
            return

        def work() -> None:
            try:
                core.apply_moves(moves, target)
                self.root.after(0, self._done_apply, len(moves))
            except Exception as exc:  # noqa: BLE001
                self.root.after(0, self._error, exc)

        self.set_busy(True)
        self.status.set("정리 중…")
        threading.Thread(target=work, daemon=True).start()

    def _done_apply(self, count: int) -> None:
        self.set_busy(False)
        self.write_log(f"✅ {count}개 파일을 정리했습니다.", clear=True)
        self.write_log("문제가 있으면 '되돌리기'를 누르세요.")
        self.status.set(f"완료: {count}개 정리됨")

    def on_undo(self) -> None:
        target = self.get_target()
        if not target:
            return
        log_path = target / core.UNDO_LOG_NAME
        if not log_path.exists():
            messagebox.showinfo("되돌리기", "이 폴더에는 되돌릴 기록이 없습니다.")
            return
        if not messagebox.askyesno("되돌리기", "마지막 정리 작업을 되돌릴까요?"):
            return

        def work() -> None:
            try:
                import json
                data = json.loads(log_path.read_text(encoding="utf-8"))
                count = len(data.get("moves", []))
                core.undo(target)
                self.root.after(0, self._done_undo, count)
            except Exception as exc:  # noqa: BLE001
                self.root.after(0, self._error, exc)

        self.set_busy(True)
        self.status.set("되돌리는 중…")
        threading.Thread(target=work, daemon=True).start()

    def _done_undo(self, count: int) -> None:
        self.set_busy(False)
        self.write_log(f"↩️ {count}개 파일을 원래 위치로 되돌렸습니다.", clear=True)
        self.status.set(f"되돌리기 완료: {count}개")

    def _error(self, exc: Exception) -> None:
        self.set_busy(False)
        messagebox.showerror("오류", str(exc))
        self.status.set("오류 발생")


def main() -> None:
    root = tk.Tk()
    OrganizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
