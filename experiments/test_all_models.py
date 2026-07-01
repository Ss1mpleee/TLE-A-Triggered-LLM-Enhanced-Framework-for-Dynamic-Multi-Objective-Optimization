import sys, time
sys.path.insert(0, "D:/新论文/实验")
from core.llm_interface import LLMClient

# Test all 3 models on the actual DE advice prompt
prompt = """You are an expert in evolutionary computation. You provide real-time
strategic advice for differential evolution (DE).

Population size: 30, Dimensions: 10, Objectives: 2
  x[0]: mean=0.50, std=0.200, range=[0.10, 0.90]
  x[1]: mean=0.45, std=0.180, range=[0.05, 0.85]
Top-3 individuals:
  rank 1: f0=0.450, f1=0.380
  rank 2: f0=0.500, f1=0.420
  rank 3: f0=0.510, f1=0.430
Total objective range: min=0.800, max=1.200

Output JSON with keys: strategy (exploit/explore/focus), F (0.1-1.0), CR (0.1-1.0), reasoning.
Return ONLY valid JSON, no markdown."""

for model in ["gemma4:26b", "qwen2.5:7b", "carstenuhlig/omnicoder-9b:q8_0"]:
    print(f"\n=== {model} ===")
    client = LLMClient(model=model, use_cache=False, max_tokens=300)
    t = time.time()
    r = client.call(prompt, temperature=0.0, force_json=True)
    elapsed = time.time() - t
    print(f"Response: {repr(r[:200])}")
    print(f"Latency: {elapsed:.2f}s")
    print(f"Out tokens: {client.get_stats()['total_tokens_out']}")
