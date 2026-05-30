# 파일 정리 프로그램 (File Organizer)

폴더 안에 어질러진 파일들을 **종류별** 또는 **날짜별**로 하위 폴더에 자동 정리해 주는 Python 프로그램입니다.
**GUI(클릭 방식)** 와 **CLI(명령어 방식)** 두 가지로 쓸 수 있습니다.

## 특징

- 🖱️ **GUI 지원**: 마우스 클릭만으로 폴더 선택 → 미리보기 → 정리
- 📂 **종류별 정리**: 이미지 / 문서 / 동영상 / 음악 / 압축파일 / 코드 등으로 자동 분류
- 📅 **날짜별 정리**: 파일 수정 날짜 기준 `2026-05` 같은 연-월 폴더로 정리
- 👀 **미리보기**: 실제로 옮기기 전에 무엇이 어디로 갈지 먼저 확인
- ↩️ **되돌리기**: 마지막 정리 작업을 한 번에 원상 복구
- 🔁 **이름 충돌 방지**: 같은 이름이 있으면 `파일 (1).jpg` 식으로 자동 처리

## 요구 사항

- Python 3.9 이상 (별도 설치 패키지 없음)
- GUI 버전은 `tkinter` 필요 — Windows/macOS 공식 Python에는 기본 포함.
  - Linux(우분투/데비안)에서 없다면: `sudo apt install python3-tk`

## 1) GUI 버전 (추천)

```bash
python organize_gui.py
```

창이 열리면:
1. **폴더 선택…** 버튼으로 정리할 폴더 고르기
2. **종류별 / 날짜별** 중 방식 선택 (필요하면 "하위 폴더 포함" 체크)
3. **👀 미리보기** 로 결과 확인
4. **✅ 정리 실행** 으로 적용 (문제가 있으면 **↩️ 되돌리기**)

> 💡 윈도우에서는 `organize_gui.py` 파일을 더블클릭해도 실행됩니다.

## 2) CLI 버전

```bash
# 미리보기 — 무엇이 정리될지만 보여줍니다 (파일을 옮기지 않음)
python organize.py ~/Downloads

# 실제로 종류별 정리 실행
python organize.py ~/Downloads --apply

# 날짜별(연-월)로 정리
python organize.py ~/Downloads --by date --apply

# 하위 폴더 파일까지 포함해서 정리
python organize.py ~/Downloads --recursive --apply

# 방금 한 정리 되돌리기
python organize.py ~/Downloads --undo
```

## 3) EXE(.exe)로 만들기 — Python 없이 더블클릭 실행

> ⚠️ `.exe`는 **Windows에서 빌드**해야 합니다. (PyInstaller는 크로스 컴파일 불가)

### 방법 A. GitHub Actions로 자동 빌드 (Windows PC 불필요, 추천)

1. GitHub 저장소의 **Actions** 탭 → **Build Windows EXE** 워크플로 선택
2. **Run workflow** 클릭 (또는 organize 파일을 푸시하면 자동 실행)
3. 실행이 끝나면 하단 **Artifacts → `FileOrganizer-windows`** 를 다운로드
4. 압축을 풀면 `FileOrganizer.exe`(GUI), `organize.exe`(CLI)가 들어 있습니다

### 방법 B. 내 Windows PC에서 직접 빌드

1. Python 3.9+ 설치 ([python.org](https://www.python.org))
2. `build_exe.bat` **더블클릭**
3. `dist\FileOrganizer.exe` 가 생성됩니다 (이 파일만 복사해 어디서나 실행 가능)

> macOS/Linux 용 실행 파일은 `bash build_exe.sh` 로 만들 수 있습니다.

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
GUI·CLI 모두 같은 핵심 로직(`organize.py`)을 공유합니다.
