#!/usr/bin/env python
"""
TLE-DMO reproduction script.

The four lines below make this script runnable from any working directory:
it puts the repository root on `sys.path` and exposes the standard result
directories as module-level `Path` constants.  Do not delete them.
"""
from __future__ import annotations
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

RAW_DIR   = REPO_ROOT / "results" / "raw"
FIG_DIR   = REPO_ROOT / "results" / "figures"
CACHE_DIR = REPO_ROOT / "results" / "llm_cache"

"""
Cross-LLM analysis: qwen2.5:7b vs qwen3.5:9b vs carstenuhlig/omnicoder-9b.

Run TLE on DF1, DF5, DF7 with 3 different LLMs to show that the
framework is model-agnostic.

Each LLM gets its own cache directory (the LLM client keys the cache
by model name, so different models get separate caches by default).

Output: RAW_DIR / "exp6_cross_llm.json"
"""
import argparse
import json
import time
import numpy as np
from pathlib import Path

from core import LLMClient, TLE, DEFAULT_MODEL
from benchmarks import DMOProblem, get_reference_pf
from core.moo_utils import compute_igd, fast_non_dominated_sort

# Default models to test
DEFAULT_MODELS = [
    'qwen2.5:7b',                       # baseline (existing)
    'qwen3.5:9b',                       # newer
    'carstenuhlig/omnicoder-9b:q8_0',  # code-specialised
]
DEFAULT_PROBS = ['DF1', 'DF5', 'DF7']
DEFAULT_SEEDS = [0, 1]
DEFAULT_POP_SIZE = 50
DEFAULT_MAX_GEN = 200


def main():
    p = argparse.ArgumentParser(
        description="Cross-LLM analysis: run TLE on multiple DMO problems with multiple Ollama models.",
    )
    p.add_argument("--models", nargs="+", default=DEFAULT_MODELS,
                   help="Ollama model names")
    p.add_argument("--problems", nargs="+", default=DEFAULT_PROBS,
                   help="DMO problems")
    p.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS,
                   help="Random seeds")
    p.add_argument("--pop-size", type=int, default=DEFAULT_POP_SIZE)
    p.add_argument("--max-gen", type=int, default=DEFAULT_MAX_GEN)
    p.add_argument("--output", type=str,
                   default=str(RAW_DIR / "exp6_cross_llm.json"))
    args = p.parse_args()

    results = []
    t_start = time.time()
    for model in args.models:
        for prob in args.problems:
            for seed in args.seeds:
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
                           pop_size=args.pop_size, max_gen=args.max_gen,
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
                results.append({
                    'model': model, 'prob': prob, 'seed': seed,
                    'igd': igd, 'invocations': inv, 'elapsed_sec': elapsed,
                })
                print(f'[{model:30s}] {prob:5s} seed={seed} '
                      f'IGD={igd:.4f} inv={inv:3d} t={elapsed:.1f}s',
                      flush=True)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'\nCross-LLM total: {time.time()-t_start:.1f}s, {len(results)} runs')
    print(f'Saved to {out}')


if __name__ == "__main__":
    main()
