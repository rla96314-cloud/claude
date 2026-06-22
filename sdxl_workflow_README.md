# SDXL 1.0 ComfyUI 워크플로우 (Civitai #101055)

[Civitai SD-XL 1.0](https://civitai.com/models/101055/sd-xl) (Base + Refiner) 용 ComfyUI 워크플로우입니다.
`sdxl_base_refiner_workflow.json` 파일을 ComfyUI 캔버스에 **드래그&드롭**(또는 `Load` 버튼)하면 바로 불러올 수 있습니다.

## 1. 모델 파일 준비

Civitai #101055 에서 받은 두 개의 체크포인트를 ComfyUI 모델 폴더에 넣으세요.

| 파일 | 위치 |
|------|------|
| `sd_xl_base_1.0.safetensors` | `ComfyUI/models/checkpoints/` |
| `sd_xl_refiner_1.0.safetensors` | `ComfyUI/models/checkpoints/` |

> 파일명이 다르면 두 `Load Checkpoint` 노드에서 직접 선택해 주세요.

## 2. 파이프라인 구조

```
[Base Checkpoint] ─ MODEL ─────────────┐
        │ CLIP ─→ CLIPTextEncodeSDXL (pos/neg)
        │ VAE ──────────────────────────────────────┐
[Empty Latent 1024x1024] ─→ KSamplerAdvanced(Base)   │
                                  │ (leftover noise)  │
                                  ▼                   │
[Refiner Checkpoint] ─ MODEL ─→ KSamplerAdvanced(Refiner) ─→ VAEDecode ─→ SaveImage
        │ CLIP ─→ CLIPTextEncodeSDXLRefiner (pos/neg)
```

- **Base 샘플러**: step 0 → 20, `add_noise=enable`, `return_with_leftover_noise=enable`
- **Refiner 샘플러**: step 20 → 끝, `add_noise=disable` (베이스의 남은 노이즈를 이어받음)
- 총 25 steps / CFG 8 / euler / normal scheduler (기본값)

## 3. 사용법

1. 위/아래 `CLIPTextEncodeSDXL` 노드의 프롬프트(긍정/부정)를 원하는 내용으로 수정합니다.
   - Refiner 쪽 프롬프트도 같은 내용으로 맞춰 주면 일관성이 좋아집니다.
2. 해상도는 SDXL 권장값인 **1024x1024**(또는 832x1216, 1216x832 등)로 두세요.
3. `Queue Prompt` 실행 → 결과는 `SaveImage`(prefix `SDXL`)로 저장됩니다.

## 팁

- VRAM 이 부족하면 Refiner 를 빼고 Base 단독(KSamplerAdvanced end_at_step=25, return_with_leftover_noise=disable)으로도 충분히 좋은 결과가 나옵니다.
- 디테일을 더 살리려면 Refiner 의 `ascore`(positive)를 6, (negative)를 2.5 부근에서 조절하세요.
