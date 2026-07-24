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

"""Trigger entropy_threshold sensitivity sweep.

The triple-signal trigger fires when entropy drop > entropy_threshold.
Sweep entropy_threshold in [0.001, 0.01, 0.05, 0.1, 0.5] on DF1+DF5
with 3 seeds, fixed scheduler (no budget cap).

Result: how does trigger sensitivity affect IGD vs invocations?
Output: results/raw/exp_trigger_threshold.json
"""
import argparse
import json
import time
import numpy as np
from pathlib import Path
from core import LLMClient, TLE, DEFAULT_MODEL
from core.bandit import FixedBudgetScheduler
from core.moo_utils import compute_igd, fast_non_dominated_sort
from benchmarks import DMOProblem, get_reference_pf

DEFAULT_PROBLEMS = ['DF1', 'DF5']
DEFAULT_SEEDS = [0, 1, 2]
DEFAULT_ENTROPY_THRESHOLDS = [0.001, 0.01, 0.05, 0.1, 0.5]
POP_SIZE = 50
MAX_GEN = 200


def run_tle_with_threshold(problem, seed, entropy_t, pop_size, max_gen):
    np.random.seed(seed)
    llm = LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True)
    algo = TLE(
        d=10, bounds=(problem.lower, problem.upper), n_obj=problem.M,
        pop_size=pop_size, max_gen=max_gen, llm=llm,
        trigger='triple', scheduler='bandit', seed=seed,
    )
    # Override trigger's entropy_threshold
    algo.trigger.entropy_threshold = entropy_t
    pop, fit, info = algo.optimize(problem.evaluate, problem=problem)
    fronts = fast_non_dominated_sort(fit)
    nd = fit[fronts[0]] if fronts else fit
    try:
        igd = float(compute_igd(nd, get_reference_pf(problem.name, n=100)))
    except Exception:
        igd = float('inf')
    return {
        'igd': igd,
        'invocations': info.get('invocations', 0),
        'elapsed_sec': info.get('elapsed_sec', 0.0),
    }


def main():
    p = argparse.ArgumentParser(
        description="Sweep the entropy threshold of the TLE trigger on selected DMO problems.",
    )
    p.add_argument("--problems", nargs="+", default=DEFAULT_PROBLEMS)
    p.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS)
    p.add_argument("--entropy-thresholds", nargs="+", type=float,
                   default=DEFAULT_ENTROPY_THRESHOLDS)
    p.add_argument("--pop-size", type=int, default=POP_SIZE)
    p.add_argument("--max-gen", type=int, default=MAX_GEN)
    p.add_argument("--output", type=str,
                   default=str(RAW_DIR / "exp_trigger_threshold.json"))
    args = p.parse_args()

    results = []
    total = len(args.problems) * len(args.seeds) * len(args.entropy_thresholds)
    done = 0
    t0 = time.time()
    for prob_name in args.problems:
        for ent_t in args.entropy_thresholds:
            for seed in args.seeds:
                t_start = time.time()
                problem = DMOProblem(name=prob_name, d=10, nt=10, taut=10)
                res = run_tle_with_threshold(
                    problem, seed, ent_t, args.pop_size, args.max_gen,
                )
                elapsed = time.time() - t_start
                done += 1
                print(f'[{done}/{total}] {prob_name} tau_e={ent_t} seed={seed}: '
                      f'IGD={res["igd"]:.4f} inv={res["invocations"]} t={elapsed:.1f}s',
                      flush=True)
                results.append({
                    'problem': prob_name,
                    'entropy_threshold': ent_t,
                    'seed': seed,
                    **res,
                })

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'\nSaved {len(results)} trigger threshold records to {out}')
    print(f'Total time: {time.time() - t0:.1f}s')


if __name__ == "__main__":
    main()