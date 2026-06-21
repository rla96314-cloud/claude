# ComfyUI 프롬프트 생성기

ComfyUI / Stable Diffusion 용 **긍정문(positive)** · **부정문(negative)** 프롬프트를
자동으로 만들어주는 작은 도구입니다. 추가 설치 없이 파이썬만 있으면 됩니다.

## 특징
- 추가 패키지 설치 불필요 (표준 라이브러리 + tkinter)
- 스타일 프리셋 3종: `realistic`(실사) / `anime`(애니) / `fantasy`(판타지·컨셉아트)
- 품질·주제·외형·장면·조명·카메라 카테고리를 조합해 자연스러운 프롬프트 구성
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
| `--subject` | 주제를 직접 지정 (없으면 라이브러리에서 선택) |
| `--shot` | 샷 크기: `closeup` `portrait` `upper-body` `medium` `cowboy` `full-body` `wide` `long` … |
| `--angle` | 앵글: `front` `side` `low` `high` `birdseye` `dutch` `pov` `behind` |
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

### 샷 · 앵글 · 표정 · 포즈 · 인원수 — GUI에서 선택하면 바로 적용
GUI 의 **샷 크기 / 앵글 / 표정**(드롭다운), **포즈**(체크, 다중),
**인원수**(라디오)를 선택하면 즉시 프롬프트에 반영됩니다.
`🎲 새로 생성(랜덤)`을 누르기 전까지는 같은 시드를 유지해 바꾼 항목만
바뀌므로 옵션 비교가 쉽습니다.

### 한글 자동 번역
GUI 의 **한글 자동 번역** 체크(기본 ON) 또는 CLI `--translate` 를 켜면
주제/주인공 칸의 한글 단어를 영어 태그로 변환합니다.
공백·쉼표로 단어를 나눠 적으세요 (예: `빨간머리 기사`, `검은머리 마법사`).
사전에 없는 한글 단어는 그대로 두고 경고를 표시합니다.

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
