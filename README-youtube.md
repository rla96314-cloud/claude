# YouTube Downloader (단독 실행형 GUI)

별도의 서버 없이 동작하는 데스크톱 YouTube 다운로더입니다. `yt-dlp` 라이브러리를
직접 호출하며, GUI 는 파이썬 표준 라이브러리인 `tkinter` 로 만들어졌습니다.
PyInstaller 로 **더블클릭만으로 실행되는 단일 실행파일**(.exe / 바이너리)로 만들 수 있습니다.

## 주요 기능

- 동영상 URL 여러 개를 한 번에 다운로드 (줄바꿈으로 구분)
- 화질/형식 선택: 최고 화질, 1080p/720p 이하, 단일 파일, 음성만(MP3)
- 저장 폴더 선택
- 실시간 진행률 표시 및 취소
- 서버·브라우저 불필요 — 완전한 오프라인 데스크톱 앱

## 1. 소스로 바로 실행하기

```bash
pip install yt-dlp
python youtube_downloader.py
```

> 고화질(영상+음성) 병합이나 MP3 변환에는 **ffmpeg** 가 필요합니다.
> ffmpeg 가 없으면 "단일 파일(병합 불필요)" 옵션만 정상 동작합니다.
> - Windows: <https://www.gyan.dev/ffmpeg/builds/> 에서 받아 PATH 에 추가
> - macOS: `brew install ffmpeg`
> - Linux: `sudo apt install ffmpeg`

## 2. 실행파일(.exe) 로 빌드하기

```bash
pip install -r requirements-youtube.txt
python build_exe.py
```

빌드가 끝나면 `dist/` 폴더에 단독 실행파일이 생성됩니다.

- Windows → `dist/YouTubeDownloader.exe`
- macOS / Linux → `dist/YouTubeDownloader`

이 파일 하나만 배포하면 됩니다. 파이썬이 설치되지 않은 컴퓨터에서도 실행됩니다.

### ffmpeg 를 실행파일에 포함하기 (선택)

`ffmpeg`(또는 Windows 의 `ffmpeg.exe`) 파일을 `build_exe.py` 와 같은 폴더에 둔 뒤
빌드하면 자동으로 실행파일 안에 함께 묶입니다. 그러면 사용자가 ffmpeg 를 따로
설치하지 않아도 고화질 병합과 MP3 변환이 동작합니다.

## 파일 구성

| 파일 | 설명 |
|------|------|
| `youtube_downloader.py` | GUI 앱 본체 |
| `build_exe.py` | PyInstaller 빌드 스크립트 |
| `requirements-youtube.txt` | 의존성 (yt-dlp, pyinstaller) |

## 주의

개인적·합법적 용도로만 사용하세요. 저작권으로 보호되는 콘텐츠의 무단 다운로드는
해당 플랫폼의 이용약관 및 관련 법률에 위배될 수 있습니다.
