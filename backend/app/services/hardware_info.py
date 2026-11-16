# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

import platform
import shutil
import subprocess
import psutil
from typing import Any, Dict


class HardwareProfiler:
    """Profiles system CPU, RAM, CUDA, and Metal accelerators,

    calculating effective usable memory for model execution recommendations.
    """

    @staticmethod
    def _detect_nvidia_gpu() -> tuple[bool, float, str | None]:
        """Detect NVIDIA GPU and VRAM using torch, or fallback to nvidia-smi."""
        # 1. Try PyTorch first
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                vram_bytes = torch.cuda.get_device_properties(0).total_memory
                return True, round(vram_bytes / (1024**3), 2), gpu_name
        except Exception:
            pass

        # 2. Fallback to nvidia-smi if torch is not installed
        if shutil.which("nvidia-smi"):
            try:
                cmd = ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"]
                out = subprocess.check_output(cmd, encoding="utf-8", timeout=2)
                lines = out.strip().splitlines()
                if lines:
                    parts = [p.strip() for p in lines[0].split(",")]
                    gpu_name = parts[0]
                    vram_mb = float(parts[1])
                    return True, round(vram_mb / 1024, 2), gpu_name
            except Exception:
                pass

        return False, 0.0, None

    @classmethod
    def get_hardware_profile(cls) -> Dict[str, Any]:
        system_os = platform.system()
        cpu_arch = platform.machine()
        physical_cores = psutil.cpu_count(logical=False) or 1
        logical_cores = psutil.cpu_count(logical=True) or 1

        # Memory profiling
        ram_info = psutil.virtual_memory()
        total_ram_gb = round(ram_info.total / (1024**3), 2)
        available_ram_gb = round(ram_info.available / (1024**3), 2)

        # Accelerator Detection (CUDA vs MPS vs CPU)
        has_cuda, cuda_vram_gb, gpu_name = cls._detect_nvidia_gpu()
        has_metal = False

        # Check Metal (Apple Silicon)
        if system_os == "Darwin" and cpu_arch == "arm64":
            has_metal = True

        # Calculate Effective Usable Memory for LLMs
        if has_cuda:
            effective_memory_gb = max(cuda_vram_gb, available_ram_gb * 0.7)
            primary_accelerator = f"CUDA ({gpu_name}, {cuda_vram_gb} GB VRAM)"
        elif has_metal:
            effective_memory_gb = available_ram_gb * 0.75
            primary_accelerator = "Apple Metal (Unified Memory)"
        else:
            effective_memory_gb = available_ram_gb * 0.5
            primary_accelerator = f"CPU Multi-Threading ({logical_cores} threads)"

        # Hardware Tier & Recommended Parameter Range
        if effective_memory_gb < 6.0:
            tier = "entry"
            rec_models = ["llama3.2:1b", "llama3.2:3b", "gemma2:2b"]
            reasoning_score, speed_score = 4, 9
        elif effective_memory_gb <= 14.0:
            tier = "mid"
            rec_models = ["llama3.1:8b", "qwen2.5:7b", "mistral:7b"]
            reasoning_score, speed_score = 7, 8
        elif effective_memory_gb <= 30.0:
            tier = "high"
            rec_models = ["qwen2.5:14b", "gemma2:9b", "mistral-nemo:12b"]
            reasoning_score, speed_score = 9, 7
        else:
            tier = "enthusiast"
            rec_models = ["qwen2.5:32b", "llama3.3:70b", "command-r:35b"]
            reasoning_score, speed_score = 10, 6

        return {
            "os": f"{system_os} ({platform.release()})",
            "architecture": cpu_arch,
            "cpu": {
                "physical_cores": physical_cores,
                "logical_cores": logical_cores,
            },
            "ram": {
                "total_gb": total_ram_gb,
                "available_gb": available_ram_gb,
            },
            "accelerator": {
                "has_cuda": has_cuda,
                "cuda_vram_gb": cuda_vram_gb,
                "has_metal": has_metal,
                "primary": primary_accelerator,
            },
            "capability_profile": {
                "effective_memory_gb": round(effective_memory_gb, 2),
                "tier": tier,
                "estimated_models": rec_models,
                "reasoning_score": reasoning_score,
                "speed_score": speed_score,
            }
        }


hardware_profiler = HardwareProfiler()
