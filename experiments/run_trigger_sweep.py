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

"""Trigger threshold sensitivity sweep.

Sweeps TLE with heuristic scheduler under different LLM budget caps
(1, 2, 3, 4, 5 calls per generation) on DF1 and DF5 with 3 seeds.

Output: results/raw/exp_trigger_sweep.json
"""
import argparse
import json
import time
import numpy as np
from pathlib import Path
from core import LLMClient, TLE, DEFAULT_MODEL
from core.bandit import HeuristicDecayScheduler
from core.moo_utils import compute_igd, fast_non_dominated_sort
from benchmarks import DMOProblem, get_reference_pf

DEFAULT_PROBLEMS = ['DF1', 'DF5']
DEFAULT_SEEDS = [0, 1, 2]
DEFAULT_BUDGET_CAPS = [1, 2, 3, 4, 5]
POP_SIZE = 50
MAX_GEN = 200


def run_tle_with_budget(problem, seed, total_budget, pop_size, max_gen):
    np.random.seed(seed)
    llm = LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True)
    algo = TLE(
        d=10, bounds=(problem.lower, problem.upper), n_obj=problem.M,
        pop_size=pop_size, max_gen=max_gen, llm=llm,
        trigger='triple', scheduler='heuristic', seed=seed,
    )
    # Override scheduler total budget
    algo.scheduler.total_budget = total_budget
    algo.scheduler.calls_made = 0
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
        description="Sweep the TLE trigger threshold / LLM budget cap on selected DMO problems.",
    )
    p.add_argument("--problems", nargs="+", default=DEFAULT_PROBLEMS,
                   help="DMO problems to sweep over")
    p.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS,
                   help="Random seeds")
    p.add_argument("--budget-caps", nargs="+", type=int,
                   default=DEFAULT_BUDGET_CAPS,
                   help="Max LLM invocations per generation to try")
    p.add_argument("--pop-size", type=int, default=POP_SIZE)
    p.add_argument("--max-gen", type=int, default=MAX_GEN)
    p.add_argument("--output", type=str,
                   default=str(RAW_DIR / "exp_trigger_sweep.json"))
    args = p.parse_args()

    results = []
    total = len(args.problems) * len(args.seeds) * len(args.budget_caps)
    done = 0
    t0 = time.time()
    for prob_name in args.problems:
        for cap in args.budget_caps:
            for seed in args.seeds:
                t_start = time.time()
                problem = DMOProblem(name=prob_name, d=10, nt=10, taut=10)
                # Heuristic decay: w0=0.5, w_t=0.5*exp(-t/T), with T=100
                # mean w_t over 200 gens is roughly 0.07, so total_budget
                # of cap*50 yields ~cap calls per gen over the first 50 gens.
                total_budget = cap * 50
                res = run_tle_with_budget(
                    problem, seed, total_budget, args.pop_size, args.max_gen,
                )
                elapsed = time.time() - t_start
                done += 1
                print(f'[{done}/{total}] {prob_name} cap~{cap}/gen budget={total_budget} seed={seed}: '
                      f'IGD={res["igd"]:.4f} inv={res["invocations"]} t={elapsed:.1f}s',
                      flush=True)
                results.append({
                    'problem': prob_name,
                    'budget_per_gen_target': cap,
                    'total_budget': total_budget,
                    'seed': seed,
                    **res,
                })

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'\nSaved {len(results)} trigger sweep records to {out}')
    print(f'Total time: {time.time() - t0:.1f}s')


if __name__ == "__main__":
    main()