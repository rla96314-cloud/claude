# ComfyUI 프롬프트 생성기

ComfyUI / Stable Diffusion 용 **긍정문(positive)** · **부정문(negative)** 프롬프트를
자동으로 만들어주는 작은 도구입니다. 추가 설치 없이 파이썬만 있으면 됩니다.

## 특징
- 추가 패키지 설치 불필요 (표준 라이브러리 + tkinter)
- 스타일 프리셋 3종: `realistic`(실사) / `anime`(애니) / `fantasy`(판타지·컨셉아트)
- 품질·주제·외형·장면·조명·카메라 카테고리를 조합해 자연스러운 프롬프트 구성
- 스타일별 맞춤 negative 프롬프트 자동 첨부
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
| `--random` / `--no-random` | 카테고리별 무작위 선택 on/off (기본 on) |
| `-n`, `--count` | 생성 개수 |
| `--seed` | 랜덤 시드 (재현용) |
| `--list` | 사용 가능한 태그 출력 |

## 커스터마이징
`comfy_prompt_generator.py` 상단의 `STYLES`, `NEGATIVE_COMMON`,
`NEGATIVE_BY_STYLE` 딕셔너리에 태그를 추가/수정하면 바로 반영됩니다.
새 스타일을 추가하려면 `STYLES` 에 같은 형식(`quality/subject/appearance/
scene/lighting/camera`)으로 항목을 하나 더 넣으면 됩니다.
