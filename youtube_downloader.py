#!/usr/bin/env python3
"""
YouTube Downloader - 단독 실행형 GUI 다운로더

- 별도의 서버가 필요 없습니다. yt-dlp 라이브러리를 직접 호출합니다.
- tkinter 기반 GUI (파이썬 표준 라이브러리).
- PyInstaller 로 단일 실행파일(.exe / 바이너리)로 빌드할 수 있습니다.

필요 패키지:
    pip install yt-dlp

(선택) 고화질 영상+오디오 병합 및 mp3 변환에는 ffmpeg 가 필요합니다.
ffmpeg 가 없으면 단일 포맷(병합 불필요) 다운로드만 사용됩니다.
"""

import os
import sys
import threading
import queue
import shutil

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


APP_TITLE = "YouTube Downloader"


def ffmpeg_dir() -> str | None:
    """번들된 ffmpeg 가 들어 있는 폴더 경로를 반환합니다 (없으면 None).

    PyInstaller onefile 빌드에서는 내장 ffmpeg 가 임시폴더(sys._MEIPASS)에
    풀리므로, 그 경로를 yt-dlp 에 ffmpeg_location 으로 넘겨줘야 인식됩니다.
    """
    exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    # 1) PyInstaller 로 묶인 ffmpeg (실행 시 _MEIPASS 에 풀림)
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass and os.path.exists(os.path.join(meipass, exe)):
        return meipass
    # 2) 스크립트/실행파일과 같은 폴더에 둔 ffmpeg
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(here, exe)):
        return here
    return None


def has_ffmpeg() -> bool:
    """시스템 PATH, 내장 번들, 또는 같은 폴더에서 ffmpeg 를 찾습니다."""
    return shutil.which("ffmpeg") is not None or ffmpeg_dir() is not None


class DownloaderApp(tk.Tk):
    """tkinter 기반 메인 윈도우."""

    # (라벨, yt-dlp format 문자열, ffmpeg 필요 여부)
    FORMAT_PRESETS = [
        ("최고 화질 (영상+음성)", "bestvideo*+bestaudio/best", True),
        ("1080p 이하", "bestvideo[height<=1080]+bestaudio/best[height<=1080]", True),
        ("720p 이하", "bestvideo[height<=720]+bestaudio/best[height<=720]", True),
        ("단일 파일(최고, 병합 불필요)", "best", False),
        ("음성만 (MP3)", "bestaudio/best", True),
    ]

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("680x540")
        self.minsize(620, 500)
        self._set_window_icon()

        self.msg_queue: "queue.Queue" = queue.Queue()
        self.download_thread = None
        self.cancel_flag = threading.Event()

        self._build_ui()
        self.after(100, self._poll_queue)

        if yt_dlp is None:
            messagebox.showerror(
                APP_TITLE,
                "yt-dlp 가 설치되어 있지 않습니다.\n\n"
                "터미널에서 다음을 실행하세요:\n    pip install yt-dlp",
            )

    def _set_window_icon(self):
        """창/작업표시줄 아이콘 설정 (icon.ico 우선, 없으면 icon.png)."""
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        ico = os.path.join(base, "icon.ico")
        png = os.path.join(base, "icon.png")
        try:
            if os.name == "nt" and os.path.exists(ico):
                self.iconbitmap(ico)
            elif os.path.exists(png):
                self._icon_img = tk.PhotoImage(file=png)
                self.iconphoto(True, self._icon_img)
        except Exception:
            pass  # 아이콘이 없어도 앱은 정상 동작

    # ------------------------------------------------------------------ UI --
    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # URL 입력
        url_frame = ttk.LabelFrame(self, text="동영상 URL (여러 개는 줄바꿈으로 구분)")
        url_frame.pack(fill="x", **pad)
        self.url_text = tk.Text(url_frame, height=4, wrap="word")
        self.url_text.pack(fill="x", padx=8, pady=8)

        # 옵션
        opt_frame = ttk.LabelFrame(self, text="옵션")
        opt_frame.pack(fill="x", **pad)

        # 저장 폴더
        ttk.Label(opt_frame, text="저장 폴더:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.folder_var = tk.StringVar(
            value=os.path.join(os.path.expanduser("~"), "Downloads")
        )
        ttk.Entry(opt_frame, textvariable=self.folder_var).grid(
            row=0, column=1, sticky="ew", padx=4, pady=6
        )
        ttk.Button(opt_frame, text="찾아보기…", command=self._choose_folder).grid(
            row=0, column=2, padx=8, pady=6
        )

        # 포맷 선택
        ttk.Label(opt_frame, text="화질/형식:").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        self.format_var = tk.StringVar(value=self.FORMAT_PRESETS[0][0])
        self.format_combo = ttk.Combobox(
            opt_frame,
            textvariable=self.format_var,
            values=[p[0] for p in self.FORMAT_PRESETS],
            state="readonly",
        )
        self.format_combo.grid(row=1, column=1, columnspan=2, sticky="ew", padx=4, pady=6)

        # 기본은 H.264(MP4) 우선. 체크하면 AV1/VP9 허용(4K 등 초고화질, 호환성↓)
        self.allow_av1_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            opt_frame,
            text="AV1/VP9 허용 (4K 등 초고화질 / 미체크 시 H.264 MP4 우선)",
            variable=self.allow_av1_var,
        ).grid(row=2, column=1, columnspan=2, sticky="w", padx=4, pady=(0, 6))

        opt_frame.columnconfigure(1, weight=1)

        # 버튼 (맨 아래에 먼저 고정 -> 내용이 많아도 절대 잘리지 않음)
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="bottom", fill="x", **pad)
        self.download_btn = ttk.Button(btn_frame, text="다운로드 시작", command=self._start_download)
        self.download_btn.pack(side="left")
        self.cancel_btn = ttk.Button(
            btn_frame, text="취소", command=self._cancel_download, state="disabled"
        )
        self.cancel_btn.pack(side="left", padx=8)

        # 진행 상태 (남는 공간을 채움)
        prog_frame = ttk.LabelFrame(self, text="진행 상태")
        prog_frame.pack(fill="both", expand=True, **pad)

        self.progress = ttk.Progressbar(prog_frame, mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=8, pady=(8, 4))

        self.status_var = tk.StringVar(value="대기 중")
        ttk.Label(prog_frame, textvariable=self.status_var).pack(anchor="w", padx=8)

        self.log_text = tk.Text(prog_frame, height=7, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)

        if not has_ffmpeg():
            self._log(
                "⚠ ffmpeg 를 찾지 못했습니다. 고화질 병합/MP3 변환이 제한됩니다.\n"
                "   '단일 파일' 옵션을 사용하거나 ffmpeg 를 설치하세요."
            )

    # ------------------------------------------------------------- handlers --
    def _choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get() or os.path.expanduser("~"))
        if folder:
            self.folder_var.set(folder)

    def _start_download(self):
        if yt_dlp is None:
            messagebox.showerror(APP_TITLE, "yt-dlp 가 설치되어 있지 않습니다.")
            return

        urls = [u.strip() for u in self.url_text.get("1.0", "end").splitlines() if u.strip()]
        if not urls:
            messagebox.showwarning(APP_TITLE, "다운로드할 URL 을 입력하세요.")
            return

        folder = self.folder_var.get().strip()
        if not folder:
            messagebox.showwarning(APP_TITLE, "저장 폴더를 선택하세요.")
            return
        os.makedirs(folder, exist_ok=True)

        preset = next(p for p in self.FORMAT_PRESETS if p[0] == self.format_var.get())
        prefer_h264 = not self.allow_av1_var.get()

        self.cancel_flag.clear()
        self.download_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.progress.config(value=0)
        self._clear_log()

        self.download_thread = threading.Thread(
            target=self._download_worker,
            args=(urls, folder, preset, prefer_h264),
            daemon=True,
        )
        self.download_thread.start()

    def _cancel_download(self):
        self.cancel_flag.set()
        self.status_var.set("취소 요청됨… 현재 항목 종료 후 중단합니다.")

    # ------------------------------------------------------------- worker ----
    def _download_worker(self, urls, folder, preset, prefer_h264=True):
        label, fmt, needs_ffmpeg = preset
        is_audio = "음성만" in label
        ffmpeg_ok = has_ffmpeg()

        if needs_ffmpeg and not ffmpeg_ok:
            self.msg_queue.put(
                ("log", f"⚠ '{label}' 은 ffmpeg 가 필요합니다. '단일 파일' 방식으로 대체합니다.")
            )
            fmt = "best"
            is_audio = False

        def hook(d):
            if self.cancel_flag.is_set():
                raise yt_dlp.utils.DownloadError("사용자에 의해 취소됨")
            status = d.get("status")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                pct = (downloaded / total * 100) if total else 0
                speed = d.get("speed") or 0
                self.msg_queue.put(("progress", pct))
                self.msg_queue.put(
                    ("status", f"다운로드 중… {pct:5.1f}%  ({speed / 1024 / 1024:.2f} MB/s)")
                )
            elif status == "finished":
                self.msg_queue.put(("status", "후처리 중… (병합/변환)"))

        ydl_opts = {
            "format": fmt,
            "outtmpl": os.path.join(folder, "%(title)s.%(ext)s"),
            "progress_hooks": [hook],
            "noprogress": True,
            "ignoreerrors": True,
            "restrictfilenames": False,
            "quiet": True,
            "no_warnings": True,
        }

        # H.264 우선(기본): yt-dlp 가 avc1(H.264) 코덱을 먼저 고르도록 정렬하고
        # mp4 컨테이너로 병합. 유튜브 H.264 는 보통 최대 1080p 이므로 그 이상은
        # 자동으로 AV1/VP9 로 떨어진다. 음성만 모드에는 적용하지 않는다.
        if prefer_h264 and not is_audio:
            ydl_opts["format_sort"] = ["vcodec:h264", "acodec:aac"]
            if ffmpeg_ok:
                ydl_opts["merge_output_format"] = "mp4"

        # 내장(또는 같은 폴더) ffmpeg 가 있으면 그 위치를 yt-dlp 에 알려준다.
        # onefile 빌드에서는 PATH 에 없으므로 이 설정이 있어야 병합/변환이 동작한다.
        _ff = ffmpeg_dir()
        if _ff:
            ydl_opts["ffmpeg_location"] = _ff

        if is_audio and ffmpeg_ok:
            ydl_opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]

        if not is_audio:
            mode = "H.264(MP4) 우선" if prefer_h264 else "AV1/VP9 허용(최고화질)"
            self.msg_queue.put(("log", f"코덱: {mode}"))

        total_count = len(urls)
        success = 0
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                for idx, url in enumerate(urls, 1):
                    if self.cancel_flag.is_set():
                        break
                    self.msg_queue.put(("log", f"[{idx}/{total_count}] {url}"))
                    self.msg_queue.put(("progress", 0))
                    try:
                        info = ydl.extract_info(url, download=True)
                        if info is not None:
                            title = info.get("title", url)
                            self.msg_queue.put(("log", f"   ✓ 완료: {title}"))
                            success += 1
                        else:
                            self.msg_queue.put(("log", "   ✗ 실패 (정보 추출 불가)"))
                    except yt_dlp.utils.DownloadError as e:
                        if self.cancel_flag.is_set():
                            self.msg_queue.put(("log", "   ■ 취소됨"))
                            break
                        self.msg_queue.put(("log", f"   ✗ 오류: {e}"))
                    except Exception as e:  # noqa: BLE001
                        self.msg_queue.put(("log", f"   ✗ 오류: {e}"))
        finally:
            done_msg = (
                f"중단됨 ({success}/{total_count} 완료)"
                if self.cancel_flag.is_set()
                else f"완료: {success}/{total_count} 개 다운로드"
            )
            self.msg_queue.put(("done", done_msg))

    # --------------------------------------------------------- queue / log --
    def _poll_queue(self):
        try:
            while True:
                kind, payload = self.msg_queue.get_nowait()
                if kind == "progress":
                    self.progress.config(value=payload)
                elif kind == "status":
                    self.status_var.set(payload)
                elif kind == "log":
                    self._log(payload)
                elif kind == "done":
                    self.status_var.set(payload)
                    self.progress.config(value=0)
                    self.download_btn.config(state="normal")
                    self.cancel_btn.config(state="disabled")
                    self._log("─" * 40)
                    self._log(payload)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _log(self, text):
        self.log_text.config(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")


def main():
    app = DownloaderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
