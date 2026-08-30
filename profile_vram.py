import gc
import json
import subprocess
import time
from typing import List, Dict, Any, Optional

from llama_cpp import Llama
from sentence_transformers import SentenceTransformer

MODEL_PATH = "d:/CODE/Hackathon/llm/Qwen2.5-7B-Instruct-Q4_K_M.gguf"
EMBEDDING_MODEL_PATH = "d:/CODE/Hackathon/llm/all-MiniLM-L6-v2"
PROMPT = "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\nWrite a long essay about the history of artificial intelligence.<|im_end|>\n<|im_start|>assistant\n"


def get_vram_usage() -> float:
    """Get the current GPU memory usage in MB using nvidia-smi."""
    try:
        result = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,nounits,noheader"],
            encoding="utf-8"
        )
        return float(result.strip())
    except Exception as e:
        print(f"Error getting VRAM: {e}")
        return 0.0


def benchmark_llm(
    n_gpu_layers: int,
    n_ctx: int,
    type_k: Optional[int] = None,
    type_v: Optional[int] = None,
    offload_kqv: bool = True
) -> Dict[str, Any]:
    """Benchmark Llama model with specific settings."""
    print(f"\n--- Testing LLM: layers={n_gpu_layers}, ctx={n_ctx}, type_k={type_k}, type_v={type_v} ---")
    
    start_vram = get_vram_usage()
    print(f"Baseline VRAM: {start_vram} MB")
    
    try:
        # Load model
        llm = Llama(
            model_path=MODEL_PATH,
            n_gpu_layers=n_gpu_layers,
            n_ctx=n_ctx,
            type_k=type_k,
            type_v=type_v,
            offload_kqv=offload_kqv,
            verbose=False,
            n_threads=4
        )
        
        load_vram = get_vram_usage()
        model_vram = load_vram - start_vram
        print(f"Model VRAM size: {model_vram} MB (Total: {load_vram} MB)")
        
        # Generate text
        start_time = time.time()
        tokens = 0
        
        # Stream output to measure tokens per second
        gen = llm(
            prompt=PROMPT,
            max_tokens=64,
            temperature=0.0,
            stream=True
        )
        
        for _ in gen:
            tokens += 1
            
        end_time = time.time()
        duration = end_time - start_time
        tps = tokens / duration
        
        final_vram = get_vram_usage()
        print(f"Final VRAM: {final_vram} MB. TPS: {tps:.2f}")
        
        # Cleanup
        del llm
        gc.collect()
        
        # Return stats
        return {
            "success": True,
            "layers": n_gpu_layers,
            "ctx": n_ctx,
            "model_vram_mb": model_vram,
            "peak_vram_mb": final_vram,
            "tps": tps
        }
    except Exception as e:
        print(f"Failed: {e}")
        return {
            "success": False,
            "layers": n_gpu_layers,
            "ctx": n_ctx,
            "error": str(e)
        }


def benchmark_embeddings(device: str) -> Dict[str, Any]:
    """Benchmark sentence transformers."""
    print(f"\n--- Testing Embeddings on {device} ---")
    start_vram = get_vram_usage()
    
    try:
        model = SentenceTransformer(EMBEDDING_MODEL_PATH, device=device)
        load_vram = get_vram_usage()
        
        start_time = time.time()
        embeddings = model.encode(["This is a test sentence."] * 32)
        end_time = time.time()
        
        final_vram = get_vram_usage()
        duration = end_time - start_time
        
        del model
        gc.collect()
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        return {
            "success": True,
            "device": device,
            "duration": duration,
            "vram_diff_mb": final_vram - start_vram
        }
    except Exception as e:
        print(f"Failed on {device}: {e}")
        return {
            "success": False,
            "device": device,
            "error": str(e)
        }


def run_sweep() -> None:
    results = []
    
    # 1. Sweep LLM layers and contexts
    for ctx in [512, 1024, 2048]:
        for layers in [18, 20, 22, 24, 26]:
            res = benchmark_llm(layers, ctx)
            results.append(res)
            time.sleep(1) # Let VRAM settle
            
            if not res["success"] and "out of memory" in res.get("error", "").lower():
                print(f"OOM hit at layers={layers}. Skipping higher layers for this ctx.")
                break
                
    # 2. Test KV Quantization (type_k=8 is Q8_0)
    print("\n--- Testing KV Quantization (Q8_0) ---")
    res = benchmark_llm(24, 2048, type_k=8, type_v=8)
    results.append(res)
    
    # 3. Test embeddings
    emb_cpu = benchmark_embeddings("cpu")
    emb_gpu = benchmark_embeddings("cuda")
    
    print("\n--- Summary ---")
    for r in results:
        if r["success"]:
            print(f"LLM: ctx={r['ctx']:>4}, layers={r['layers']:>2} | VRAM peak: {r['peak_vram_mb']:>6.1f} MB | TPS: {r['tps']:.2f}")
        else:
            print(f"LLM: ctx={r['ctx']:>4}, layers={r['layers']:>2} | FAILED: {r.get('error')}")
            
    print(f"Embeddings CPU: {emb_cpu}")
    print(f"Embeddings GPU: {emb_gpu}")
    

if __name__ == "__main__":
    run_sweep()
