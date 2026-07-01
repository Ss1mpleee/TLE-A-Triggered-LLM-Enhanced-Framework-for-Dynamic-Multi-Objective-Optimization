import sys, time
sys.path.insert(0, "D:/新论文/实验")
import numpy as np
from core.llm_interface import LLMClient
from core.prompts import call_llm_for_advice

# Test with different LLMs
for model in ["qwen2.5:7b", "gemma4:26b"]:
    print(f"\n=== {model} on real TLE prompt ===")
    client = LLMClient(model=model, use_cache=False, max_tokens=400)
    np.random.seed(42)
    pop = np.random.uniform(0, 1, (50, 10))
    fit = np.column_stack([np.sum(pop**2, axis=1), 1 - np.sum(pop**2, axis=1)])
    bounds = (np.zeros(10), np.ones(10))
    t = time.time()
    advice = call_llm_for_advice(client, pop, fit, bounds, generation=10)
    elapsed = time.time() - t
    print(f"Advice: {advice}")
    print(f"Latency: {elapsed:.2f}s")
    print(f"Out tokens: {client.get_stats()['total_tokens_out']}")
