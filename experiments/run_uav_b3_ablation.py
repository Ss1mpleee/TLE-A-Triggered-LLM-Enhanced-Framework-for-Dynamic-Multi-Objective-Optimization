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
B3: Per-action ablation experiment.

For each of the 4 multi-action controller actions, run an "only-this-action"
variant (LLM is restricted to picking only that action). This shows the
contribution of each action separately.

Variants:
  - TLE-only-param              (LLM restricted to 'param' action)
  - TLE-only-archive_reset      (LLM restricted to 'archive_reset')
  - TLE-only-restart_top        (LLM restricted to 'restart_top')
  - TLE-only-diversity_injection (LLM restricted to 'diversity_injection')
  - TLE-full                    (LLM picks freely, the main TLE-MA)

Baselines:
  - DE                          (no LLM, no trigger)
  - DNSGA-II-A                  (classical diversity-injection)

Hypothesis:
  - Each single-action variant should underperform TLE-full (showing
    that the action space diversity matters).
  - TLE-full should beat each single-action variant by 5-15%.

Test fleet sizes: 8, 16, 32-UAV (where B6 showed TLE wins)
Seeds: 5 (0-4) for time efficiency; can extend to 30 if results show
"""
import json
import time
import argparse
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from core import (
    LLMClient, DEBaseline, DNSGAIIA, TLEMultiAction,
    DEFAULT_MODEL,
)
from benchmarks.uav_scenario import (
    ScenarioConfig, generate_scenario, evaluate_uav_solution,
)
from core.moo_utils import fast_non_dominated_sort, compute_hv


ABLATION_ALGOS = [
    "TLE-only-param",
    "TLE-only-archive_reset",
    "TLE-only-restart_top",
    "TLE-only-diversity_injection",
    "TLE-full",
]
BASELINE_ALGOS = ["DE", "DNSGA-II-A"]
ALL_ALGOS = ABLATION_ALGOS + BASELINE_ALGOS


def encode_uav_chromosome(pop, scenario):
    NP, D = pop.shape
    n_uavs = int(np.sqrt(D))
    while n_uavs * n_uavs < D:
        n_uavs += 1
    n_tasks = D // n_uavs
    actual_D = n_uavs * n_tasks
    if actual_D != D:
        pop = pop[:, :actual_D]
        D = actual_D
    fits = np.zeros((NP, 3))
    for i in range(NP):
        fits[i] = evaluate_uav_solution(pop[i], scenario)
    return fits


def run_algo(algo_name, D, scenario, pop_size, max_gen, llm_model, seed, budget=40):
    np.random.seed(seed)
    use_llm = algo_name.startswith("TLE")
    llm = (LLMClient(model=llm_model, max_tokens=400, use_cache=True)
           if use_llm else None)
    bounds = (np.zeros(D), np.ones(D))

    if algo_name == "DE":
        algo = DEBaseline(d=D, bounds=bounds, n_obj=3, pop_size=pop_size,
                          max_gen=max_gen, seed=seed)
    elif algo_name == "DNSGA-II-A":
        algo = DNSGAIIA(d=D, bounds=bounds, n_obj=3, pop_size=pop_size,
                        max_gen=max_gen, seed=seed)
    elif algo_name.startswith("TLE-"):
        # Parse out restrict_actions
        if algo_name == "TLE-full":
            restrict = None
        else:
            action = algo_name.split("TLE-only-")[1]
            restrict = [action]
        algo = TLEMultiAction(
            d=D, bounds=bounds, n_obj=3, pop_size=pop_size,
            max_gen=max_gen, llm=llm,
            trigger="triple", scheduler="fixed", budget=budget,
            restrict_actions=restrict, seed=seed,
        )
    else:
        raise ValueError(f"Unknown algo: {algo_name}")

    def evaluate(pop):
        return encode_uav_chromosome(pop, scenario)

    t0 = time.time()
    pop, fit, info = algo.optimize(evaluate)
    elapsed = time.time() - t0

    fronts = fast_non_dominated_sort(fit)
    nd_fit = fit[fronts[0]] if fronts else fit
    f1_value = -np.min(nd_fit[:, 0]) if len(nd_fit) else 0
    f2_time = -np.min(nd_fit[:, 1]) if len(nd_fit) else 600
    f3_battery = -np.max(nd_fit[:, 2]) if len(nd_fit) else 0

    return {
        "algo": algo_name,
        "seed": seed,
        "n_uavs": scenario.get("n_uavs", 0),
        "n_tasks": len(scenario["tasks"]),
        "f1_value": float(f1_value),
        "f2_response_time": float(f2_time),
        "f3_battery": float(f3_battery),
        "elapsed_sec": float(elapsed),
        "invocations": info.get("invocations", 0),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--algos", nargs="+", default=ALL_ALGOS)
    parser.add_argument("--n-uavs", nargs="+", type=int, default=[8, 16, 32])
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2, 3, 4])
    parser.add_argument("--budget", type=int, default=40,
                        help="LLM invocation budget per run")
    parser.add_argument("--model", type=str, default="qwen2.5:7b")
    parser.add_argument("--output", type=str,
                        default=r"D:\新论文\实验\results\raw\exp3_uav_b3.json")
    args = parser.parse_args()

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    if Path(args.output).exists():
        all_results = json.load(open(args.output, encoding='utf-8'))
        print(f"[load] Loaded {len(all_results)} existing results")
    else:
        all_results = []

    done_keys = {(r['algo'], r['n_uavs'], r['seed']) for r in all_results}
    print(f"[skip] Already have {len(done_keys)} (algo, n_uavs, seed) tuples")

    pending = []
    for algo in args.algos:
        for nu in args.n_uavs:
            for seed in args.seeds:
                if (algo, nu, seed) not in done_keys:
                    pending.append((algo, nu, seed))

    print(f"\n=== Plan: {len(pending)} new runs ===")
    print(f"Algos: {args.algos}")
    print(f"n_uavs: {args.n_uavs}")
    print(f"Seeds: {args.seeds}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    if not pending:
        print("Nothing to do, all runs already complete.")
        return

    t_start = time.time()
    for i, (algo, nu, seed) in enumerate(pending, 1):
        cfg = ScenarioConfig(
            n_uavs=nu,
            simulation_time=300.0,
            task_arrival_rate=0.3,
            seed=seed,
        )
        scenario = generate_scenario(cfg)
        scenario["n_uavs"] = nu
        n_tasks = len(scenario["tasks"])
        D = nu * n_tasks
        # pop_size scales with n_uavs (consistent with B6)
        pop_size = 30 if nu == 8 else (60 if nu == 16 else 100)

        print(f"[{i}/{len(pending)}] {algo:35s} n_uavs={nu} seed={seed} D={D}")
        t0 = time.time()
        try:
            result = run_algo(algo, D, scenario, pop_size, 40, args.model, seed, args.budget)
            elapsed = time.time() - t0
            print(f"  -> value={result['f1_value']:.1f}, "
                  f"time={result['f2_response_time']:.1f}s, "
                  f"inv={result['invocations']}, took {elapsed:.1f}s")
            all_results.append(result)

            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            continue

        elapsed_total = time.time() - t_start
        avg_per_run = elapsed_total / i
        eta = avg_per_run * (len(pending) - i)
        print(f"  total elapsed: {elapsed_total/60:.1f}m, ETA: {eta/60:.1f}m")

    print(f"\n=== Done: {len(pending)} runs in {(time.time()-t_start)/3600:.2f}h ===")
    print(f"Output: {args.output} ({len(all_results)} total records)")


if __name__ == "__main__":
    main()