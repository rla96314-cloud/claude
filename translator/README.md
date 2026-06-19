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
