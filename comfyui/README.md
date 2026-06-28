# ComfyUI 배경 생성 워크플로우

SDXL 기반의 텍스트-투-이미지 워크플로우입니다. 16:9 와이드 비율의 배경 이미지를
생성하도록 구성되어 있어, VJ / 인터랙티브 아트 / 무대 배경 등에 바로 쓰기 좋습니다.
(이 저장소의 심박 → OSC 연동 같은 라이브 비주얼 작업의 배경 소스로 활용하세요.)

## 파일

| 파일 | 용도 |
|------|------|
| `background_workflow.json` | ComfyUI 웹 UI에서 **Load** 로 불러오는 워크플로우 |
| `background_workflow_api.json` | `/prompt` API(`POST`)로 직접 큐에 넣는 API 포맷 |

## 사용법 (웹 UI)

1. ComfyUI 실행 후 우측 메뉴 또는 상단의 **Load** 클릭
2. `background_workflow.json` 선택
3. `CheckpointLoaderSimple` 노드의 체크포인트를 본인이 보유한 SDXL 모델로 변경
   (기본값: `sd_xl_base_1.0.safetensors`)
4. 긍정/부정 프롬프트 수정 후 **Queue Prompt**
5. 결과는 `ComfyUI/output/` 에 `background_xxxxx.png` 로 저장됩니다

## 사용법 (API)

```bash
curl -X POST http://127.0.0.1:8188/prompt \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": $(cat background_workflow_api.json)}"
```

## 주요 파라미터

| 노드 | 파라미터 | 기본값 | 설명 |
|------|----------|--------|------|
| EmptyLatentImage | width × height | 1344 × 768 | SDXL 친화적 16:9 해상도 |
| KSampler | steps | 30 | 샘플링 스텝 |
| KSampler | cfg | 7.0 | 프롬프트 반영 강도 |
| KSampler | sampler / scheduler | dpmpp_2m / karras | 안정적인 기본 조합 |
| KSampler | seed | 0 (UI에서 randomize) | 매번 다른 배경을 원하면 randomize 유지 |

## 팁

- **다른 비율**: 세로 배경은 768 × 1344, 정사각형은 1024 × 1024 로 변경
- **모델 없음**: SDXL 모델이 없다면 `sd_xl_base_1.0.safetensors` 를
  `ComfyUI/models/checkpoints/` 에 받아 넣으세요
- **인물 제거**: 부정 프롬프트에 이미 `person, people, face, character` 가 포함되어
  순수 배경 위주로 생성됩니다
- **업스케일**: 더 큰 해상도가 필요하면 VAEDecode 뒤에 `UpscaleModelLoader` +
  `ImageUpscaleWithModel` 노드를 추가하세요
