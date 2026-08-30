"""GPU and VRAM hardware diagnostics utility for PyTorch/CUDA runtime."""
from __future__ import annotations

from typing import Any
from backend.logger.app_logger import get_logger

logger = get_logger("engine.gpu_diagnostics")


def get_gpu_memory_info() -> dict[str, Any]:
    """Inspect CUDA hardware availability and current VRAM allocation."""
    try:
        import torch

        if not torch.cuda.is_available():
            return {
                "cuda_available": False,
                "device_name": "CPU",
                "device_count": 0,
                "allocated_mb": 0.0,
                "reserved_mb": 0.0,
                "total_mb": 0.0,
            }

        dev_idx = torch.cuda.current_device()
        dev_name = torch.cuda.get_device_name(dev_idx)
        alloc_bytes = torch.cuda.memory_allocated(dev_idx)
        res_bytes = torch.cuda.memory_reserved(dev_idx)
        props = torch.cuda.get_device_properties(dev_idx)
        total_bytes = getattr(props, "total_memory", 0)

        return {
            "cuda_available": True,
            "device_name": dev_name,
            "device_count": torch.cuda.device_count(),
            "allocated_mb": round(alloc_bytes / (1024 * 1024), 2),
            "reserved_mb": round(res_bytes / (1024 * 1024), 2),
            "total_mb": round(total_bytes / (1024 * 1024), 2),
        }
    except (ImportError, RuntimeError, OSError) as exc:
        logger.warning(f"GPU Diagnostics: Unable to query CUDA runtime ({type(exc).__name__}: {exc})")
        return {
            "cuda_available": False,
            "device_name": "Unknown",
            "device_count": 0,
            "allocated_mb": 0.0,
            "reserved_mb": 0.0,
            "total_mb": 0.0,
        }


def log_startup_vram_status(phase: str = "boot") -> dict[str, Any]:
    """Log current VRAM and CUDA memory diagnostics at specific boot phases."""
    info = get_gpu_memory_info()
    if info["cuda_available"]:
        logger.info(
            f"VRAM Diagnostics [{phase}]: {info['device_name']} "
            f"(Allocated: {info['allocated_mb']} MiB, Reserved: {info['reserved_mb']} MiB, "
            f"Total: {info['total_mb']} MiB)"
        )
    else:
        logger.info(f"VRAM Diagnostics [{phase}]: CUDA not active (Running on CPU execution mode)")
    return info
