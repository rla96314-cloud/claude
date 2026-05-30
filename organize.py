#!/usr/bin/env python3
"""파일 정리 프로그램 (File Organizer)

폴더 안의 파일들을 종류별(이미지, 문서, 동영상 등) 또는 날짜별로
하위 폴더에 자동 정리합니다.

사용 예시:
    python organize.py ~/Downloads                 # 미리보기 후 종류별 정리
    python organize.py ~/Downloads --apply         # 실제로 정리 실행
    python organize.py ~/Downloads --by date --apply
    python organize.py ~/Downloads --undo          # 직전 정리 되돌리기
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

# 확장자 -> 분류 폴더 이름 매핑
CATEGORIES: dict[str, set[str]] = {
    "이미지": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp",
             ".svg", ".heic", ".ico", ".raw"},
    "문서": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".hwp",
            ".md", ".tex", ".pages"},
    "스프레드시트": {".xls", ".xlsx", ".csv", ".ods", ".numbers"},
    "프레젠테이션": {".ppt", ".pptx", ".odp", ".key"},
    "동영상": {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v"},
    "음악": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"},
    "압축파일": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
    "코드": {".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".go", ".rs",
            ".rb", ".php", ".html", ".css", ".json", ".xml", ".yml", ".yaml",
            ".sh", ".sql"},
    "실행파일": {".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".app"},
    "폰트": {".ttf", ".otf", ".woff", ".woff2"},
}

OTHER_FOLDER = "기타"          # 분류되지 않은 파일
UNDO_LOG_NAME = ".organize_undo.json"  # 실행 취소용 기록 파일


def category_for(extension: str) -> str:
    """확장자에 해당하는 분류 폴더 이름을 반환한다."""
    ext = extension.lower()
    for folder, extensions in CATEGORIES.items():
        if ext in extensions:
            return folder
    return OTHER_FOLDER


def plan_moves(target: Path, by: str, recursive: bool) -> list[tuple[Path, Path]]:
    """이동 계획((원본, 대상) 목록)을 만든다. 실제로 옮기지는 않는다."""
    known_folders = set(CATEGORIES.keys()) | {OTHER_FOLDER}
    files = target.rglob("*") if recursive else target.iterdir()
    moves: list[tuple[Path, Path]] = []

    for item in files:
        if not item.is_file():
            continue
        if item.name == UNDO_LOG_NAME:
            continue
        # 이미 정리된 분류 폴더 안의 파일은 건드리지 않는다
        if item.parent.name in known_folders:
            continue

        if by == "type":
            subfolder = category_for(item.suffix)
        else:  # by == "date" : 수정 날짜 기준 연-월 폴더
            mtime = datetime.fromtimestamp(item.stat().st_mtime)
            subfolder = mtime.strftime("%Y-%m")

        dest_dir = target / subfolder
        dest = unique_path(dest_dir / item.name, planned={m[1] for m in moves})
        moves.append((item, dest))

    return moves


def unique_path(dest: Path, planned: set[Path]) -> Path:
    """이름이 겹치면 'name (1).ext' 형태로 충돌을 피한 경로를 만든다."""
    if not dest.exists() and dest not in planned:
        return dest
    stem, suffix = dest.stem, dest.suffix
    counter = 1
    while True:
        candidate = dest.with_name(f"{stem} ({counter}){suffix}")
        if not candidate.exists() and candidate not in planned:
            return candidate
        counter += 1


def apply_moves(moves: list[tuple[Path, Path]], target: Path) -> None:
    """계획된 이동을 실제로 수행하고 실행 취소 기록을 남긴다."""
    record: list[dict[str, str]] = []
    for src, dest in moves:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        record.append({"from": str(src), "to": str(dest)})

    log_path = target / UNDO_LOG_NAME
    log_path.write_text(
        json.dumps({"timestamp": datetime.now().isoformat(), "moves": record},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def undo(target: Path) -> int:
    """직전 정리 작업을 되돌린다."""
    log_path = target / UNDO_LOG_NAME
    if not log_path.exists():
        print(f"되돌릴 기록이 없습니다: {log_path}")
        return 1

    data = json.loads(log_path.read_text(encoding="utf-8"))
    moves = data.get("moves", [])
    restored = 0
    # 역순으로 복원
    for entry in reversed(moves):
        src, dest = Path(entry["to"]), Path(entry["from"])
        if not src.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        final = unique_path(dest, planned=set())
        shutil.move(str(src), str(final))
        restored += 1

    log_path.unlink()
    # 비어 있는 분류 폴더 정리
    remove_empty_dirs(target)
    print(f"{restored}개 파일을 원래 위치로 되돌렸습니다.")
    return 0


def remove_empty_dirs(target: Path) -> None:
    """target 바로 아래의 빈 폴더를 삭제한다."""
    for child in target.iterdir():
        if child.is_dir() and not any(child.iterdir()):
            child.rmdir()


def print_plan(moves: list[tuple[Path, Path]]) -> None:
    """이동 계획을 보기 좋게 출력한다."""
    if not moves:
        print("정리할 파일이 없습니다.")
        return
    grouped: dict[str, int] = {}
    for _, dest in moves:
        folder = dest.parent.name
        grouped[folder] = grouped.get(folder, 0) + 1

    print(f"\n총 {len(moves)}개 파일을 정리합니다:")
    for folder in sorted(grouped):
        print(f"  📁 {folder}/  ({grouped[folder]}개)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="폴더 안의 파일을 종류별/날짜별로 정리합니다.",
    )
    parser.add_argument("path", help="정리할 폴더 경로")
    parser.add_argument("--by", choices=["type", "date"], default="type",
                        help="정리 기준: type(종류별, 기본값) 또는 date(날짜별)")
    parser.add_argument("--apply", action="store_true",
                        help="실제로 파일을 이동한다 (없으면 미리보기만)")
    parser.add_argument("--recursive", action="store_true",
                        help="하위 폴더의 파일까지 포함한다")
    parser.add_argument("--undo", action="store_true",
                        help="직전 정리 작업을 되돌린다")

    args = parser.parse_args(argv)
    target = Path(args.path).expanduser().resolve()

    if not target.is_dir():
        print(f"오류: 폴더를 찾을 수 없습니다 -> {target}", file=sys.stderr)
        return 1

    if args.undo:
        return undo(target)

    moves = plan_moves(target, by=args.by, recursive=args.recursive)
    print_plan(moves)

    if not moves:
        return 0

    if args.apply:
        apply_moves(moves, target)
        print("\n✅ 정리 완료! 되돌리려면 다음을 실행하세요:")
        print(f"   python organize.py \"{target}\" --undo")
    else:
        print("\n(미리보기입니다. 실제로 정리하려면 --apply 옵션을 추가하세요.)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
