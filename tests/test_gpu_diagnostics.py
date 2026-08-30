"""Unit tests for GPU and VRAM diagnostics utility."""
from __future__ import annotations

from unittest.mock import MagicMock
import pytest
from backend.engine.gpu_diagnostics import get_gpu_memory_info, log_startup_vram_status


def test_gpu_memory_info_structure() -> None:
    """Test get_gpu_memory_info returns dictionary with expected keys."""
    info = get_gpu_memory_info()
    assert isinstance(info, dict)
    assert "cuda_available" in info
    assert "device_name" in info
    assert "allocated_mb" in info
    assert "reserved_mb" in info
    assert "total_mb" in info


def test_gpu_memory_info_mock_cuda(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test GPU memory info when CUDA is reported available."""
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = True
    mock_torch.cuda.current_device.return_value = 0
    mock_torch.cuda.get_device_name.return_value = "NVIDIA GeForce RTX 3050 Laptop GPU"
    mock_torch.cuda.device_count.return_value = 1
    mock_torch.cuda.memory_allocated.return_value = 524288000  # ~500 MiB
    mock_torch.cuda.memory_reserved.return_value = 1048576000  # ~1000 MiB
    props = MagicMock()
    props.total_memory = 6442450944  # 6144 MiB
    mock_torch.cuda.get_device_properties.return_value = props

    monkeypatch.setattr("torch.cuda.is_available", mock_torch.cuda.is_available)
    monkeypatch.setattr("torch.cuda.current_device", mock_torch.cuda.current_device)
    monkeypatch.setattr("torch.cuda.get_device_name", mock_torch.cuda.get_device_name)
    monkeypatch.setattr("torch.cuda.device_count", mock_torch.cuda.device_count)
    monkeypatch.setattr("torch.cuda.memory_allocated", mock_torch.cuda.memory_allocated)
    monkeypatch.setattr("torch.cuda.memory_reserved", mock_torch.cuda.memory_reserved)
    monkeypatch.setattr("torch.cuda.get_device_properties", mock_torch.cuda.get_device_properties)

    info = get_gpu_memory_info()
    assert info["cuda_available"] is True
    assert "RTX 3050" in info["device_name"]
    assert info["allocated_mb"] == 500.0
    assert info["reserved_mb"] == 1000.0
    assert info["total_mb"] == 6144.0


def test_log_startup_vram_status_logging() -> None:
    """Test log_startup_vram_status executes and returns memory info."""
    res = log_startup_vram_status("test_phase")
    assert isinstance(res, dict)
    assert "cuda_available" in res
