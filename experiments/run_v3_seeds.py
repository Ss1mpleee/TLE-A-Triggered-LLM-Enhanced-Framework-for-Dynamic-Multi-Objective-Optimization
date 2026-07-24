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

"""Add seeds 5-9 (5 additional seeds) to sec_main + UAV experiments.

This expands the sample size from 5 to 10 seeds for stronger statistical
power.  Existing sec_main_v2.json has seeds [0,1,2,3,4]; we add [5,6,7,8,9]
and merge into sec_main_v3.json.

With LLM cache, the runtime is dominated by non-LLM baselines (DE, PPS,
DNSGA-II-A) which run in ~1s each.  Estimated total: 5 algos × 5 probs ×
5 new seeds × ~5s/run = ~10 min for main.  UAV: ~5 min.
"""
import json
import time
import numpy as np
from pathlib import Path
from collections import defaultdict

from core import LLMClient, TLE, DEBaseline, PPSDMOEA, DNSGAIIA, DEFAULT_MODEL
from core.bandit import HeuristicDecayScheduler
from benchmarks import DMOProblem, get_reference_pf
from core.moo_utils import compute_igd, compute_hv, fast_non_dominated_sort

RAW = Path(r'D:\新论文\实验\results\raw')
RAW.mkdir(parents=True, exist_ok=True)

# Config
ALGOS = ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A', 'TLE']
PROBS = ['DF1', 'DF2', 'DF3', 'DF5', 'DF7']
NEW_SEEDS = [5, 6, 7]
POP_SIZE = 50
MAX_GEN = 200
D = 10


def make_algo(algo_name, llm, seed):
    lower = np.zeros(D)
    upper = np.ones(D)
    if algo_name == "DE":
        return DEBaseline(d=D, bounds=(lower, upper), n_obj=2,
                          pop_size=POP_SIZE, max_gen=MAX_GEN,
                          F=0.5, CR=0.9, strategy="rand", seed=seed)
    elif algo_name == "DE-LM-static-trigger":
        return TLE(d=D, bounds=(lower, upper), n_obj=2,
                   pop_size=POP_SIZE, max_gen=MAX_GEN, llm=llm,
                   trigger="triple", scheduler="heuristic",
                   budget=20, seed=seed)
    elif algo_name == "PPS-DMOEA":
        return PPSDMOEA(d=D, bounds=(lower, upper), n_obj=2,
                        pop_size=POP_SIZE, max_gen=MAX_GEN,
                        F=0.5, CR=0.9, seed=seed, predict_ratio=0.5)
    elif algo_name == "DNSGA-II-A":
        return DNSGAIIA(d=D, bounds=(lower, upper), n_obj=2,
                        pop_size=POP_SIZE, max_gen=MAX_GEN,
                        eta_c=20, eta_m=20, immigrant_frac=0.2, seed=seed)
    else:  # TLE
        return TLE(d=D, bounds=(lower, upper), n_obj=2,
                   pop_size=POP_SIZE, max_gen=MAX_GEN, llm=llm,
                   trigger="triple", scheduler="bandit", seed=seed)


def run_main_extra():
    """Run additional seeds 5-9 on main DMO problems."""
    # Load existing v2 data
    out_main = RAW / 'sec_main_v3.json'
    if out_main.exists():
        results = json.load(open(out_main, encoding='utf-8'))
    else:
        # Seed from v2
        v2 = json.load(open(RAW / 'sec_main_v2.json', encoding='utf-8'))
        results = v2
        # Also include MOEA/DD if present
        moeadd_fp = RAW / 'exp4_moeadd.json'
        if moeadd_fp.exists():
            moeadd = json.load(open(moeadd_fp, encoding='utf-8'))
            results.extend(moeadd)
        print(f'Seeded from v2: {len(results)} existing records')

    # Track which (algo, prob, seed) we've already done
    done = {(r['algo'], r['problem'], r['seed']) for r in results if 'problem' in r}
    print(f'Already have {len(done)} runs in v3 base')

    llm = LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True)
    new_runs = 0
    t_start = time.time()

    for seed in NEW_SEEDS:
        for prob in PROBS:
            np.random.seed(seed)
            problem = DMOProblem(name=prob, d=D, nt=10, taut=10)
            ref_pf = get_reference_pf(prob, n=100)
            lower = problem.lower
            upper = problem.upper

            def evaluate(pop):
                return problem.evaluate(pop)

            for algo in ALGOS:
                key = (algo, prob, seed)
                if key in done:
                    continue
                # Recreate problem & algo
                np.random.seed(seed)
                problem = DMOProblem(name=prob, d=D, nt=10, taut=10)
                ref_pf = get_reference_pf(prob, n=100)
                bounds = (problem.lower, problem.upper)
                a = make_algo(algo, llm, seed)
                # Update bounds for problem-specific lower/upper
                a.bounds = bounds
                # Reconstruct if has separate d
                if hasattr(a, 'pop_size'):
                    pass  # use existing
                t0 = time.time()
                pop, fit, info = a.optimize(evaluate, problem=problem)
                elapsed = time.time() - t0
                # IGD
                fronts = fast_non_dominated_sort(fit)
                nd_fit = fit[fronts[0]] if fronts else fit
                try:
                    igd = float(compute_igd(nd_fit, ref_pf))
                except Exception:
                    igd = float('inf')
                # HV
                try:
                    hv = float(compute_hv(nd_fit, np.array([1.1, 1.1])))
                except Exception:
                    hv = 0.0
                r = {
                    "algo": algo,
                    "problem": prob,
                    "seed": seed,
                    "igd": igd,
                    "hv": hv,
                    "invocations": info.get("invocations", 0),
                    "elapsed_sec": elapsed,
                }
                results.append(r)
                new_runs += 1
                print(f'  [seed={seed}] {algo:22s} {prob:5s} '
                      f'IGD={igd:.4f} inv={r["invocations"]:3d} ({elapsed:.1f}s)')
                # Save incrementally
                with open(out_main, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

    print(f'\nMain v3: {new_runs} new runs in {time.time()-t_start:.1f}s '
          f'(total {len(results)} runs)')


if __name__ == "__main__":
    run_main_extra()