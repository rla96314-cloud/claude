"""Optimization nodes for ComfyUI.

These nodes target the three things that usually bottleneck a ComfyUI run:

* VRAM headroom   -> ``VRAMCleanup``, ``AdaptiveBatchSize``
* Compute speed   -> ``TorchPerfTuner``, ``ModelMemoryFormat``
* Batch ergonomics-> ``BatchLatentGenerator``, ``BatchSeedList``

Everything degrades gracefully: if CUDA isn't present, the nodes become
no-ops that still pass their inputs through, so a workflow built on a GPU box
still loads on a CPU-only machine.
"""

import gc

import torch

import comfy.model_management as mm


# --------------------------------------------------------------------------- #
# Wildcard type — lets a socket accept/emit any ComfyUI type.
# ComfyUI matches on string equality, so a type that compares equal to
# everything ("*") is the canonical way to build passthrough/anchor sockets.
# --------------------------------------------------------------------------- #
class AnyType(str):
    def __eq__(self, _other):
        return True

    def __ne__(self, _other):
        return False

    def __hash__(self):
        return hash("*")


ANY = AnyType("*")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _free_total_vram_mb():
    """Return (free, total) VRAM in MiB for the active device, or (0, 0)."""
    if not torch.cuda.is_available():
        return 0.0, 0.0
    free, total = torch.cuda.mem_get_info()
    return free / 1024 ** 2, total / 1024 ** 2


def _empty_cache():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


# --------------------------------------------------------------------------- #
# VRAM cleanup
# --------------------------------------------------------------------------- #
class VRAMCleanup:
    """Free cached VRAM and (optionally) unload models mid-graph.

    Insert this between memory-heavy stages — e.g. after the KSampler and
    before a VAE decode / upscale — to reclaim the sampler's working set.
    The ``passthrough`` input exists only to anchor this node in the graph so
    execution order is deterministic.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "passthrough": (ANY,),
                "unload_models": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = (ANY,)
    RETURN_NAMES = ("passthrough",)
    FUNCTION = "clean"
    CATEGORY = "optimizer"
    OUTPUT_NODE = False

    def clean(self, passthrough, unload_models):
        before, total = _free_total_vram_mb()
        if unload_models:
            mm.unload_all_models()
        mm.soft_empty_cache()
        _empty_cache()
        after, _ = _free_total_vram_mb()
        if total:
            print(
                f"[optimizer] VRAMCleanup: freed {after - before:.0f} MiB "
                f"({after:.0f}/{total:.0f} MiB free)"
            )
        return (passthrough,)


# --------------------------------------------------------------------------- #
# Torch performance tuner
# --------------------------------------------------------------------------- #
class TorchPerfTuner:
    """Toggle global Torch performance switches.

    * ``tf32``         — allow TF32 matmul/conv on Ampere+ (big speedup, tiny
                         precision cost; safe for diffusion).
    * ``cudnn_benchmark`` — let cuDNN autotune kernels. Worth it when input
                         shapes are stable across a batch; counterproductive if
                         resolutions change every run.

    Place it once at the top of the graph; wire its output anywhere downstream
    so it runs before sampling.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "anchor": (ANY,),
                "tf32": ("BOOLEAN", {"default": True}),
                "cudnn_benchmark": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = (ANY,)
    RETURN_NAMES = ("anchor",)
    FUNCTION = "tune"
    CATEGORY = "optimizer"

    def tune(self, anchor, tf32, cudnn_benchmark):
        torch.backends.cuda.matmul.allow_tf32 = tf32
        torch.backends.cudnn.allow_tf32 = tf32
        torch.backends.cudnn.benchmark = cudnn_benchmark
        print(
            f"[optimizer] TorchPerfTuner: tf32={tf32} "
            f"cudnn_benchmark={cudnn_benchmark}"
        )
        return (anchor,)


# --------------------------------------------------------------------------- #
# Model memory format
# --------------------------------------------------------------------------- #
class ModelMemoryFormat:
    """Convert a model's conv weights to ``channels_last``.

    On NVIDIA tensor cores this speeds up the UNet's convolutions with no
    quality change. Returns the same MODEL object so it slots transparently
    between a loader and the sampler.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "enable": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("MODEL",)
    FUNCTION = "apply"
    CATEGORY = "optimizer"

    def apply(self, model, enable):
        if enable:
            try:
                model.model.to(memory_format=torch.channels_last)
                print("[optimizer] ModelMemoryFormat: channels_last applied")
            except Exception as exc:  # noqa: BLE001 - never break the graph
                print(f"[optimizer] ModelMemoryFormat skipped: {exc}")
        return (model,)


# --------------------------------------------------------------------------- #
# Adaptive batch size
# --------------------------------------------------------------------------- #
class AdaptiveBatchSize:
    """Pick a batch size that fits the current free VRAM.

    Estimates per-image cost from resolution and a model-class multiplier, then
    clamps to ``[1, max_batch]`` leaving a safety reserve. Feed the INT output
    into ``BatchLatentGenerator`` (or any ``batch_size`` socket).
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "max_batch": ("INT", {"default": 8, "min": 1, "max": 256}),
                "model_class": (["sd15", "sdxl", "flux"],),
                "vram_reserve_mb": ("INT", {"default": 1536, "min": 0, "max": 65536}),
            }
        }

    RETURN_TYPES = ("INT", "STRING")
    RETURN_NAMES = ("batch_size", "report")
    FUNCTION = "compute"
    CATEGORY = "optimizer"

    # Rough working-set cost per megapixel, per image, in MiB.
    _COST_PER_MP = {"sd15": 320.0, "sdxl": 650.0, "flux": 1100.0}

    def compute(self, width, height, max_batch, model_class, vram_reserve_mb):
        free, total = _free_total_vram_mb()
        megapixels = (width * height) / 1_000_000.0
        per_image = self._COST_PER_MP[model_class] * max(megapixels, 0.01)

        if free <= 0:  # CPU / unknown -> trust the user's ceiling
            batch = max_batch
            report = f"No CUDA info; using max_batch={max_batch}"
        else:
            usable = max(free - vram_reserve_mb, 0.0)
            batch = int(usable // per_image)
            batch = max(1, min(batch, max_batch))
            report = (
                f"{model_class} @ {width}x{height} ~{per_image:.0f} MiB/img, "
                f"{usable:.0f} MiB usable ({free:.0f}/{total:.0f} free) "
                f"-> batch={batch}"
            )
        print(f"[optimizer] AdaptiveBatchSize: {report}")
        return (batch, report)


# --------------------------------------------------------------------------- #
# Batch latent generator
# --------------------------------------------------------------------------- #
class BatchLatentGenerator:
    """Empty latents with channel layout chosen by model class.

    SD1.5/SDXL use 4-channel /8 latents; Flux uses 16-channel /8. This saves
    wiring the right ``EmptyLatentImage`` variant and keeps the batch size in
    one place for the optimizer chain.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 256}),
                "model_class": (["sd15", "sdxl", "flux"],),
            }
        }

    RETURN_TYPES = ("LATENT",)
    FUNCTION = "generate"
    CATEGORY = "optimizer"

    def generate(self, width, height, batch_size, model_class):
        channels = 16 if model_class == "flux" else 4
        device = mm.intermediate_device()
        latent = torch.zeros(
            [batch_size, channels, height // 8, width // 8], device=device
        )
        return ({"samples": latent},)


# --------------------------------------------------------------------------- #
# Batch seed list
# --------------------------------------------------------------------------- #
class BatchSeedList:
    """Deterministic, reproducible seeds for a batch.

    Produces ``base_seed, base_seed+1, ...`` (or all identical) and reports them
    as a string so a batch run is fully reproducible from a single seed value.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
                "batch_size": ("INT", {"default": 4, "min": 1, "max": 256}),
                "mode": (["increment", "fixed"],),
            }
        }

    RETURN_TYPES = ("INT", "STRING")
    RETURN_NAMES = ("seed", "seed_list")
    FUNCTION = "build"
    CATEGORY = "optimizer"

    def build(self, base_seed, batch_size, mode):
        if mode == "fixed":
            seeds = [base_seed] * batch_size
        else:
            seeds = [base_seed + i for i in range(batch_size)]
        return (base_seed, ", ".join(str(s) for s in seeds))


NODE_CLASS_MAPPINGS = {
    "OptimizerVRAMCleanup": VRAMCleanup,
    "OptimizerTorchPerfTuner": TorchPerfTuner,
    "OptimizerModelMemoryFormat": ModelMemoryFormat,
    "OptimizerAdaptiveBatchSize": AdaptiveBatchSize,
    "OptimizerBatchLatentGenerator": BatchLatentGenerator,
    "OptimizerBatchSeedList": BatchSeedList,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OptimizerVRAMCleanup": "🧹 VRAM Cleanup",
    "OptimizerTorchPerfTuner": "⚡ Torch Perf Tuner",
    "OptimizerModelMemoryFormat": "🧩 Model Memory Format",
    "OptimizerAdaptiveBatchSize": "📐 Adaptive Batch Size",
    "OptimizerBatchLatentGenerator": "🗂️ Batch Latent Generator",
    "OptimizerBatchSeedList": "🎲 Batch Seed List",
}
