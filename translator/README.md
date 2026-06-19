# 로컬 한↔영 번역기 (Ollama)

인터넷 없이 로컬에서 동작하는 한국어 ↔ 영어 데스크톱 번역기입니다.
번역은 [Ollama](https://ollama.com)로 띄운 로컬 LLM이 담당하며, 모든 요청은
`http://localhost:11434` 의 로컬 서버로만 전송됩니다. (외부 API 호출 없음)

UI는 파이썬 표준 라이브러리 `tkinter`로 만들어서 **추가 파이썬 패키지 설치가
필요 없습니다.** (HTTP 호출도 표준 `urllib` 사용)

## 준비물

1. **Ollama 설치 및 실행**
   - https://ollama.com 에서 설치 후 실행 (백그라운드에서 서버가 뜸)

2. **번역용 모델 받기** — 한·영 모두 잘하는 모델 추천:
   ```bash
   ollama pull qwen2.5:7b      # 추천 (한국어 품질 좋음, ~4.7GB)
   # 또는
   ollama pull gemma2:9b
   ollama pull llama3.1:8b
   ```

3. **tkinter** (대부분의 데스크톱 파이썬에 기본 포함)
   - Ubuntu/Debian에서 없다면: `sudo apt install python3-tk`
   - macOS(공식 python.org)/Windows: 기본 포함

## 실행

```bash
python3 translator.py
```

## 사용법

- **방향**: `한국어 → English`, `English → 한국어`, `자동 감지` 중 선택
- **모델**: 설치된 모델이 자동으로 목록에 뜸 (`새로고침`으로 갱신)
- 입력창에 텍스트를 넣고 **번역하기** 버튼 또는 **Ctrl+Enter**
- **결과 복사** 버튼으로 클립보드에 복사

## EXE로 빌드해서 바탕화면에 올리기 (윈도우)

`translator.py`는 파이썬 스크립트라 평소엔 `python3 translator.py`로 실행하지만,
**더블클릭으로 실행되는 단독 `.exe`** 로 만들 수도 있습니다.

1. 이 `translator` 폴더를 윈도우 PC로 복사 (또는 이 저장소를 clone)
2. 폴더 안의 **`build_windows.bat` 를 더블클릭**

그러면 자동으로:
- PyInstaller 설치
- `한영번역기.exe` 빌드 (`--onefile --windowed`)
- **바탕화면에 `한영번역기.exe` 복사**

빌드가 끝나면 바탕화면의 `한영번역기.exe`를 더블클릭해 실행하면 됩니다.
(단, 번역하려면 Ollama가 실행 중이어야 합니다.)

> **참고**
> - 빌드는 반드시 **윈도우 PC에서** 해야 윈도우 exe가 나옵니다. (리눅스/맥에서
>   빌드하면 해당 OS용 실행파일이 됩니다.)
> - exe는 파이썬/tkinter를 내장하므로, 빌드 후엔 파이썬 설치 없이도 실행됩니다.
>   하지만 **Ollama는 여전히 별도로 설치/실행**되어 있어야 합니다.
> - 직접 빌드하려면: `pyinstaller --onefile --windowed --name 한영번역기 translator.py`
> - **윈도우 시작 시 자동 실행**을 원하면, 만들어진 exe의 바로가기를
>   `Win+R` → `shell:startup` 폴더에 넣으면 됩니다.

## 동작 방식

`translator.py` 한 파일로 구성되어 있습니다.

- `fetch_models()` — `/api/tags`로 설치된 모델 목록 조회
- `build_prompt()` — 방향에 맞는 번역 지시 프롬프트 생성
- `translate()` — `/api/generate`로 번역 요청 (temperature 0.2로 일관성 ↑)
- 번역은 백그라운드 스레드에서 실행되어 GUI가 멈추지 않습니다.

## 문제 해결

| 증상 | 해결 |
|------|------|
| "Ollama에 연결 못함" | Ollama 실행 여부 확인, 터미널에서 `ollama list` 동작하는지 확인 |
| 모델 목록이 비어 있음 | `ollama pull qwen2.5:7b` 로 모델을 먼저 받기 |
| `ModuleNotFoundError: tkinter` | `sudo apt install python3-tk` (리눅스) |
| 번역이 느림 | 더 작은 모델 사용 (예: `qwen2.5:3b`) 또는 GPU 사용 |
