"""Run the full n=30 cross-LLM experiment in background.

3 models × 3 problems × 30 seeds = 270 runs. Estimated ~3 hours.
Saves to results/raw/exp6_cross_llm_n30.json (preserves the n=2 pilot file).

Prints progress to stdout (captured by run_in_background).
"""
import json, time
import numpy as np
from pathlib import Path
import sys

# Make repo root importable
REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from core import LLMClient, TLE, DEFAULT_MODEL
from benchmarks import DMOProblem, get_reference_pf
from core.moo_utils import compute_igd, fast_non_dominated_sort

OUT = REPO / "results" / "raw" / "exp6_cross_llm_n30.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

MODELS = [
    "qwen2.5:7b",
    "qwen3.5:9b",
    "carstenuhlig/omnicoder-9b:q8_0",
]
PROBS = ["DF1", "DF5", "DF7"]
SEEDS = list(range(30))  # 0-29

print(f"Cross-LLM n=30 plan:")
print(f"  {len(MODELS)} models × {len(PROBS)} problems × {len(SEEDS)} seeds = {len(MODELS)*len(PROBS)*len(SEEDS)} runs")
print(f"  Output: {OUT}")
print()

results = []
t_start = time.time()
total_runs = len(MODELS) * len(PROBS) * len(SEEDS)
done = 0

for model in MODELS:
    for prob in PROBS:
        for seed in SEEDS:
            np.random.seed(seed)
            problem = DMOProblem(name=prob, d=10, nt=10, taut=10)
            ref_pf = get_reference_pf(prob, n=100)
            bounds = (problem.lower, problem.upper)

            def evaluate(pop):
                return problem.evaluate(pop)

            llm = LLMClient(model=model, max_tokens=500, use_cache=True)
            llm.reset_stats()
            algo = TLE(d=10, bounds=bounds, n_obj=problem.M,
                       pop_size=50, max_gen=200,
                       llm=llm, trigger='triple', scheduler='bandit',
                       seed=seed)
            t0 = time.time()
            pop, fit, info = algo.optimize(evaluate, problem=problem)
            elapsed = time.time() - t0
            fronts = fast_non_dominated_sort(fit)
            nd = fit[fronts[0]] if fronts else fit
            try:
                igd = float(compute_igd(nd, ref_pf))
            except Exception:
                igd = float('inf')
            inv = info.get('invocations', 0)
            cache_hits = llm.cache_hits
            results.append({
                'model': model, 'prob': prob, 'seed': seed,
                'igd': igd, 'invocations': inv, 'elapsed_sec': elapsed,
                'cache_hits': cache_hits,
            })
            done += 1
            elapsed_total = time.time() - t_start
            eta = elapsed_total / done * (total_runs - done)
            print(f"[{done:3d}/{total_runs}] [{model:30s}] {prob:5s} seed={seed:2d} "
                  f"IGD={igd:.4f} inv={inv:3d} cache={cache_hits:3d} "
                  f"t={elapsed:5.1f}s (total {elapsed_total/60:5.1f}m, ETA {eta/60:5.1f}m)",
                  flush=True)
            # Periodic save (every 10 runs)
            if done % 10 == 0:
                with open(OUT, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

# Final save
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nDone: {len(results)} runs in {(time.time()-t_start)/60:.1f} min")
print(f"Saved to {OUT}")
