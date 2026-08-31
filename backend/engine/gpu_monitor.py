"""GPU hardware telemetry monitoring via background task."""
import asyncio
import subprocess
import torch
from backend.logger.app_logger import get_logger
from backend.metrics import GPU_VRAM_USAGE, GPU_TEMPERATURE

logger = get_logger("engine.gpu_monitor")

def _get_gpu_temperature() -> float | None:
    """Sync function to get GPU temperature."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"], 
            capture_output=True, text=True, check=True
        )
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError, OSError):
        return None

async def poll_gpu_metrics() -> None:
    """Background task polling GPU metrics every 30 seconds."""
    while True:
        try:
            if torch.cuda.is_available():
                GPU_VRAM_USAGE.set(torch.cuda.memory_allocated(0))
                temp = await asyncio.to_thread(_get_gpu_temperature)
                if temp is not None:
                    GPU_TEMPERATURE.set(temp)
        except (RuntimeError, OSError) as exc:
            logger.warning(f"GPU metrics poll error: {exc}")
        await asyncio.sleep(30)
