"""Cross-LLM analysis: qwen2.5:7b vs qwen3.5:9b vs carstenuhlig/omnicoder-9b.

Run TLE on DF5 and DF7 with 3 different LLMs to show that the
framework is model-agnostic.  We also run on DF1 (the easiest)
to test the boundary.

Each LLM gets a fresh cache directory (otherwise it would inherit
the qwen2.5 cache and would not exercise the new model).

Output: 实验/results/raw/exp6_cross_llm.json
"""
import sys
sys.path.insert(0, r'D:\新论文\实验')

import json
import time
import numpy as np
from pathlib import Path

from core import LLMClient, TLE, DEFAULT_MODEL
from benchmarks import DMOProblem, get_reference_pf
from core.moo_utils import compute_igd, fast_non_dominated_sort

# Models to test
MODELS = [
    'qwen2.5:7b',                   # baseline (existing)
    'qwen3.5:9b',                   # newer
    'carstenuhlig/omnicoder-9b:q8_0',  # code-specialised
]

PROBS = ['DF1', 'DF5', 'DF7']   # 3 problems × 3 models × 2 seeds
SEEDS = [0, 1]
POP_SIZE = 50
MAX_GEN = 200

results = []
t_start = time.time()
for model in MODELS:
    for prob in PROBS:
        for seed in SEEDS:
            np.random.seed(seed)
            problem = DMOProblem(name=prob, d=10, nt=10, taut=10)
            ref_pf = get_reference_pf(prob, n=100)
            bounds = (problem.lower, problem.upper)

            def evaluate(pop):
                return problem.evaluate(pop)

            # Cache is keyed by model name in the LLM client,
            # so different models get separate caches.
            llm = LLMClient(model=model, max_tokens=500, use_cache=True)
            llm.reset_stats()
            algo = TLE(d=10, bounds=bounds, n_obj=problem.M,
                       pop_size=POP_SIZE, max_gen=MAX_GEN, llm=llm,
                       trigger='triple', scheduler='bandit', seed=seed)
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
            cache_stats = llm.stats() if hasattr(llm, 'stats') else {}
            results.append({
                'model': model, 'prob': prob, 'seed': seed,
                'igd': igd, 'invocations': inv, 'elapsed_sec': elapsed,
            })
            print(f'[{model:30s}] {prob:5s} seed={seed} '
                  f'IGD={igd:.4f} inv={inv:3d} t={elapsed:.1f}s', flush=True)

out = Path(r'D:\新论文\实验\results\raw\exp6_cross_llm.json')
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f'\nCross-LLM total: {time.time()-t_start:.1f}s, {len(results)} runs')
print(f'Saved to {out}')
