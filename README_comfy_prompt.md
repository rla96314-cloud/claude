# ComfyUI 프롬프트 생성기

ComfyUI / Stable Diffusion 용 **긍정문(positive)** · **부정문(negative)** 프롬프트를
자동으로 만들어주는 도구입니다.

세 가지 형태로 쓸 수 있습니다:

| 파일 | 형태 | 설치 |
|------|------|------|
| `prompt_studio.py` | **Prompt Studio** — 다크 테마 GUI (권장) | `pip install customtkinter` |
| `comfy_prompt_generator.py` | 기본 tkinter GUI / CLI | 불필요(표준 라이브러리) |
| `PromptStudio.exe` | 윈도우 단독 실행 파일 | 불필요 |

생성·번역 엔진은 `comfy_prompt_generator.py` 한 곳에 있고, Prompt Studio 는
그 엔진을 재사용하는 모던 UI 입니다.

## Prompt Studio (다크 GUI)
```bash
pip install customtkinter
python prompt_studio.py
```
- 다크 테마 + 접이식 설정 섹션(스타일 / 인물 / 배경 / 구도·카메라 / 조명 /
  감정·분위기 / 의상·소품 / 기타)
- 인물(인물·성별·연령·특징), 배경(장소·배경설명), 의상·소품을 세분화 입력
- 샷·앵글·프레이밍·조명·시간·감정·분위기 드롭다운, 무채색/흑백/강조 토글
- 우측 Prompt / Negative Prompt 패널(글자수 표시, 지우기·복사), 저장·불러오기
- `한글번역` 기본 ON (온라인+사전 폴백)

### 윈도우 .exe 빌드
**A. GitHub Actions (권장, 윈도우 PC 불필요)**
브랜치에 push 하면 `Build Prompt Studio (Windows .exe)` 워크플로가 윈도우
러너에서 빌드합니다. 저장소 **Actions 탭 → 해당 실행 → Artifacts** 에서
`PromptStudio-windows` 를 내려받으면 `PromptStudio.exe` 가 들어 있습니다.
(수동 실행: Actions 탭에서 `Run workflow`)

**B. 로컬 빌드 (윈도우)**
```bat
pip install -r requirements-studio.txt
pyinstaller --onefile --windowed --name PromptStudio --collect-all customtkinter prompt_studio.py
```
→ `dist\PromptStudio.exe` 생성.

## 기본 생성기 (comfy_prompt_generator.py)

추가 설치 없이 파이썬만 있으면 되는 가벼운 버전입니다.

## 특징
- 추가 패키지 설치 불필요 (표준 라이브러리 + tkinter)
- 스타일 프리셋 4종: `realistic`(실사) / `anime`(애니) / `fantasy`(판타지·컨셉아트) /
  `creature`(크리쳐·몬스터 디자인)
- 품질·주제·외형·장면·조명·카메라 카테고리를 조합해 자연스러운 프롬프트 구성
- **인물 / 배경 / 상황**을 각각 따로 입력 (비우면 자동 생성)
- **샷 / 앵글 / 표정 / 포즈 / 인원수** 옵션을 선택하면 즉시 반영
- 스타일별 맞춤 negative 프롬프트 자동 첨부
- 다수 인물에서 **주인공 지정**(가중치 + `solo focus`) 지원
- **한글 입력 → 영어 태그 자동 번역** (예: `빨간머리 기사` → `red hair knight`)
- **GUI** 와 **CLI** 둘 다 지원

## 실행

### GUI (기본)
```bash
python comfy_prompt_generator.py
```
스타일 선택 → (선택) 주제 입력 → `🎲 생성` → `Positive/Negative 복사` 로
ComfyUI 의 CLIP Text Encode 노드에 그대로 붙여넣기.

### CLI
```bash
# 실사 인물, 주제 직접 지정
python comfy_prompt_generator.py --cli --style realistic --subject "1girl, long hair"

# 애니 스타일 랜덤 5개
python comfy_prompt_generator.py --cli --style anime --random -n 5

# 같은 결과 재현이 필요하면 시드 지정
python comfy_prompt_generator.py --cli --style fantasy --seed 123

# 스타일/태그 목록 보기
python comfy_prompt_generator.py --cli --list
```

| 옵션 | 설명 |
|------|------|
| `--style` | `realistic` / `anime` / `fantasy` (기본 realistic) |
| `--character` | 인물 묘사 (예: `"korean girl, long black hair"`) |
| `--background` | 배경/장소 (예: `"rainy neon city"`) |
| `--situation` | 상황/행동/분위기 (예: `"drinking coffee, relaxed"`) |
| `--subject` | (구) 단일 주제 — `--character` 의 별칭(하위호환) |
| `--shot` | 샷 크기: `closeup` `portrait` `upper-body` `cowboy` `full-body` `wide` `long` `back-full` `back-upper` `back-closeup` … |
| `--angle` | 앵글: `front` `side` `low` `high` `birdseye` `dutch` `fisheye` `wide-angle` `three-quarter` `overhead` `looking-up` `pov` `behind` |
| `--no-emphasis` | 샷/앵글 가중치 강조 끄기 (기본은 강조 ON) |
| `--emph-weight` | 강조 가중치 값 (기본 1.4, 예: 1.6 더 강하게) |
| `--expr` | 표정: `smile` `happy` `serious` `sad` `angry` `surprised` `shy` `wink` `crying` … |
| `--pose` | 포즈 (여러 번 사용 가능): `standing` `sitting` `action` `dancing` `fighting` … |
| `--count` | 인원수: `solo` `2` `3` `4` `crowd` (기본 solo) |
| `--main` | 다수일 때 주인공 묘사 (solo면 자동으로 2명으로 올림) |
| `--main-focus` | 주인공에 가중치 + `solo focus` 로 강조 |
| `--translate` | 주제/주인공의 한글을 영어 태그로 자동 변환 |
| `--no-random` | 무작위 대신 대표 태그 사용 |
| `-n` | 생성 개수 |
| `--seed` | 랜덤 시드 (재현용) |
| `--list` | 사용 가능한 옵션/태그 출력 |
| `--help-main` | 주인공 지정 방법 설명 출력 |

> 정확한 슬러그 목록은 `--list` 로 언제든 확인할 수 있습니다.

### 인물 · 배경 · 상황 — 따로 입력
주제를 하나로 뭉뚱그리지 않고 **인물**(누가), **배경**(어디서), **상황**(무엇을/
분위기)을 각각 적습니다. 비워두면 자동으로 채워집니다.
- **인물**을 적으면 모델이 임의로 외형을 섞지 않습니다(충돌 방지).
- **배경**을 적으면 랜덤 배경 대신 그 배경이 쓰입니다.
- **상황**은 행동·분위기 태그로 들어갑니다.
예) 인물 `korean girl, black hair` / 배경 `rainy neon city` /
상황 `drinking coffee, relaxed`

### 뒷모습 & 시점 강조
- 샷 크기에 **뒷모습 전신/상반신/클로즈업**(`back-full`/`back-upper`/
  `back-closeup`)을 추가했습니다. `from behind, ... , back view` 가 함께 들어가
  뒷모습이 더 잘 잡힙니다.
- 앵글에 **어안(fisheye) · 광각(wide-angle) · 3/4 시점 · 정수리뷰 · 올려다봄**
  등을 추가했습니다.
- **시점·샷 강조(가중치)** 가 기본 ON 이라, 선택한 샷/앵글이 `(태그:1.4)` 로
  강하게 주입됩니다. 잘 안 먹으면 `--emph-weight 1.6` 처럼 더 올리세요.

### 샷 · 앵글 · 표정 · 포즈 · 인원수 — GUI에서 선택하면 바로 적용
GUI 의 **샷 크기 / 앵글 / 표정**(드롭다운), **포즈**(체크, 다중),
**인원수**(라디오)를 선택하면 즉시 프롬프트에 반영됩니다.
`🎲 새로 생성(랜덤)`을 누르기 전까지는 같은 시드를 유지해 바꾼 항목만
바뀌므로 옵션 비교가 쉽습니다.

### 한글 자동 번역
GUI 의 **한글 자동 번역** 체크(기본 ON) 또는 CLI `--translate` 를 켜면
주제/주인공 칸의 한글을 영어로 변환합니다.

- **온라인 우선**: 인터넷이 되면 구글 번역으로 임의의 한글 문장도 번역
  (예: `일본인, 건방진 성격, 탁한 노란색` → `japanese, arrogant personality,
  muddy yellow`). GUI 에 `🌐 온라인 번역 적용됨` 으로 표시됩니다.
- **오프라인 폴백**: 인터넷이 막혀 있으면 내장 사전(약 200단어: 머리색·눈·
  직업·종족·의상·색·국적·성격 등)으로 단어 단위 변환. 사전에 없는 단어는
  그대로 두고 경고합니다. (`📖 오프라인 사전 번역 적용됨`)
- CLI 에서 온라인을 끄려면 `--offline-translate` 사용.
- 타이핑 중에는 약 0.6초 멈출 때만 번역을 호출(디바운스)해 매 글자마다
  네트워크를 두드리지 않습니다. 같은 문구는 캐시되어 재번역하지 않습니다.

> 구글 비공식 엔드포인트라 환경에 따라 차단될 수 있으며, 그 경우 자동으로
> 내장 사전으로 폴백합니다. 사전에 단어를 추가하려면 `KO_EN` 딕셔너리에
> `"한글": "english"` 한 줄을 넣으세요.

### 다수 인물에서 '주인공' 정하기
인원수를 2명 이상으로 설정하면 **👑 주인공 지정** 칸이 활성화됩니다.
주인공 묘사를 입력하고 **주인공 강조**를 켜면 다음이 자동 적용됩니다.

```
2people, (red-haired knight:1.3), solo focus, looking at viewer, ...
```

주인공을 정하는 5가지 방법(순서·가중치·`solo focus`·`BREAK`·리저널 프롬프트)은
GUI의 `❔ 주인공 지정 방법` 버튼 또는 `--help-main` 으로 볼 수 있습니다.
가장 확실한 방법은 ComfyUI의 **리저널 프롬프트**(영역 분리) 노드
(`Attention Couple`, `Regional Prompter`, 기본 `Conditioning (Set Area)` +
`Conditioning (Combine)`)로 인물별 프롬프트를 화면 영역마다 따로 적용하는 것입니다.

## 커스터마이징
`comfy_prompt_generator.py` 상단의 `STYLES`, `NEGATIVE_COMMON`,
`NEGATIVE_BY_STYLE` 딕셔너리에 태그를 추가/수정하면 바로 반영됩니다.
새 스타일을 추가하려면 `STYLES` 에 같은 형식(`quality/subject/appearance/
scene/lighting/camera`)으로 항목을 하나 더 넣으면 됩니다.
