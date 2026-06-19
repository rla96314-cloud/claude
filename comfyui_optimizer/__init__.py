"""ComfyUI Optimizer — custom nodes for VRAM/throughput optimization and batching.

Drop this folder into ``ComfyUI/custom_nodes/`` and restart ComfyUI.
The nodes appear under the ``optimizer/`` category.
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

# ComfyUI looks for this when serving any bundled JS (none here, but kept for convention).
WEB_DIRECTORY = "./web"
