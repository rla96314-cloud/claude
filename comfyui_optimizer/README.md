# ComfyUI Optimizer

A small pack of ComfyUI custom nodes for **VRAM management, performance tuning,
and batch generation**, plus a ready-to-run batch-optimized SDXL workflow.

## Install

```bash
git clone <this-repo> ComfyUI/custom_nodes/comfyui_optimizer
# or copy the comfyui_optimizer/ folder into ComfyUI/custom_nodes/
```

Restart ComfyUI. The nodes show up under the **`optimizer/`** category.
No extra dependencies — only `torch` and ComfyUI's own modules.

## Nodes

| Node | What it does | Typical placement |
|------|--------------|-------------------|
| ⚡ **Torch Perf Tuner** | Enables TF32 + cuDNN autotune globally. | Once near the start of the graph. |
| 🧩 **Model Memory Format** | Converts the UNet to `channels_last` for faster convs on tensor cores. | Between the checkpoint loader and the sampler. |
| 📐 **Adaptive Batch Size** | Reads free VRAM and picks a safe batch size for the resolution + model class. | Feeds `batch_size` into the latent generator. |
| 🗂️ **Batch Latent Generator** | Empty latents with the right channel count (4 for SD/SDXL, 16 for Flux). | Replaces `EmptyLatentImage`. |
| 🎲 **Batch Seed List** | Reproducible incrementing/fixed seeds for the whole batch. | Feeds `seed` into the KSampler. |
| 🧹 **VRAM Cleanup** | Frees cached VRAM (optionally unloads models) mid-graph. | Between the sampler and VAE decode/upscale. |

All nodes degrade to no-ops on CPU-only machines, so workflows stay portable.

## Batch-optimized workflow

`workflows/batch_optimized_sdxl.json` wires everything together:

```
Checkpoint ─▶ Model Memory Format ─▶ KSampler ─▶ VRAM Cleanup ─▶ VAE Decode ─▶ Save
Adaptive Batch Size ─▶ Batch Latent Generator ─▶ Torch Perf Tuner ─▶ (KSampler)
Batch Seed List ─▶ (KSampler seed)
```

Load it via **ComfyUI → Load** and point the checkpoint loader at your SDXL
model. Adaptive Batch Size will size the batch to your card automatically; drop
`max_batch` if you want a hard ceiling.

### Tuning tips
- Keep `cudnn_benchmark` on only when resolution is constant across runs.
- Raise `vram_reserve_mb` if you also run a VAE/upscale step after sampling.
- For Flux, switch the `model_class` dropdowns on the batch nodes to `flux`.

## Z-Image Turbo workflow (8 GB-friendly)

`workflows/zimage_turbo_optimized.json` is tuned for **Z-Image Turbo**, the
distilled few-step model — ideal for 8 GB cards.

Required files:

| File | Folder |
|------|--------|
| `z_image_turbo_bf16.safetensors` | `models/diffusion_models/` |
| `qwen_3_4b.safetensors`          | `models/text_encoders/` |
| `ae.safetensors`                 | `models/vae/` |

Loaders: `UNETLoader` + `CLIPLoader` (type **lumina2**) + `VAELoader`.
Sampler: **8 steps, CFG 1.0, `res_multistep` / `simple`**.

> ⚠️ Z-Image Turbo runs at CFG 1.0, so the **negative prompt is disabled**
> (`ConditioningZeroOut`). Steer quality/anatomy through the *positive* prompt.
> For negative prompts to take effect, use the non-turbo Z-Image at CFG > 1.

Optimizer nodes included here: `Torch Perf Tuner` (TF32 helps the DiT matmuls),
`Adaptive Batch Size`, `Batch Seed List`, and `VRAM Cleanup` before VAE decode.
`Model Memory Format` is intentionally omitted — `channels_last` only helps
conv UNets, not Z-Image's transformer.
