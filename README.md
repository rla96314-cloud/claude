# 파일 정리 프로그램 (File Organizer)

폴더 안에 어질러진 파일들을 **종류별** 또는 **날짜별**로 하위 폴더에 자동 정리해 주는 Python 프로그램입니다.

## 특징

- 📂 **종류별 정리**: 이미지 / 문서 / 동영상 / 음악 / 압축파일 / 코드 등으로 자동 분류
- 📅 **날짜별 정리**: 파일 수정 날짜 기준 `2026-05` 같은 연-월 폴더로 정리
- 👀 **미리보기**: 실제로 옮기기 전에 무엇이 어디로 갈지 먼저 확인 (기본값)
- ↩️ **되돌리기**: 마지막 정리 작업을 한 번에 원상 복구
- 🔁 **이름 충돌 방지**: 같은 이름이 있으면 `파일 (1).jpg` 식으로 자동 처리

## 요구 사항

- Python 3.9 이상 (별도 설치 패키지 없음)

## 사용법

```bash
# 1) 미리보기 — 무엇이 정리될지만 보여줍니다 (파일을 옮기지 않음)
python organize.py ~/Downloads

# 2) 실제로 종류별 정리 실행
python organize.py ~/Downloads --apply

# 3) 날짜별(연-월)로 정리
python organize.py ~/Downloads --by date --apply

# 4) 하위 폴더 파일까지 포함해서 정리
python organize.py ~/Downloads --recursive --apply

# 5) 방금 한 정리 되돌리기
python organize.py ~/Downloads --undo
```

> 💡 처음 쓸 때는 `--apply` 없이 먼저 미리보기로 확인한 뒤 실행하는 것을 권장합니다.

## 분류 종류

| 폴더 | 포함 확장자(예시) |
|------|------------------|
| 이미지 | jpg, png, gif, webp, heic … |
| 문서 | pdf, docx, txt, hwp, md … |
| 스프레드시트 | xls, xlsx, csv … |
| 프레젠테이션 | ppt, pptx, key … |
| 동영상 | mp4, mov, mkv, avi … |
| 음악 | mp3, wav, flac, m4a … |
| 압축파일 | zip, rar, 7z, tar … |
| 코드 | py, js, html, json … |
| 실행파일 | exe, dmg, deb … |
| 폰트 | ttf, otf, woff … |
| 기타 | 위에 해당하지 않는 모든 파일 |

분류 기준을 바꾸고 싶으면 `organize.py` 상단의 `CATEGORIES` 사전을 수정하면 됩니다.
