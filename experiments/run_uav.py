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
UAV Scenario Experiment
=======================
Run all algorithms on dynamic multi-UAV task allocation.
"""
import json
import time
import argparse
import numpy as np
from pathlib import Path
from datetime import datetime

from core import (
    LLMClient, TLE, DEBaseline,
    StaticLMEABaseline, RandomLMEABaseline,
    DEFAULT_MODEL,
)
from benchmarks import (
    ScenarioConfig, generate_scenario,
    evaluate_uav_solution, decode_chromosome_to_assignment,
)
from core.moo_utils import fast_non_dominated_sort, compute_hv


ALGORITHMS = {
    "DE": dict(trigger="never", scheduler="bandit"),
    "DE-LM-always": dict(trigger="always", scheduler="fixed"),
    "DE-LM-random": dict(trigger="random", scheduler="fixed"),
    "TLE": dict(trigger="triple", scheduler="bandit"),
}


def encode_uav_chromosome(pop):
    """Convert each individual to assignment matrix and evaluate."""
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
        fits[i] = evaluate_uav_solution(pop[i], _current_scenario)
    return fits


_current_scenario = None


def run_uav_experiment(
    seeds=(0, 1, 2),
    n_uavs=4,
    pop_size=30,
    max_gen=40,
    llm_model=DEFAULT_MODEL,
    output_file=str(RAW_DIR / "exp3_uav.json"),
):
    """Run UAV scenario experiment."""
    global _current_scenario
    results = []

    # 5 algos × 3 seeds = 15 runs (DE-LM-always without LLM to save time)
    for seed in seeds:
        # Build scenario
        cfg = ScenarioConfig(
            n_uavs=n_uavs,
            simulation_time=300.0,
            task_arrival_rate=0.3,
            seed=seed,
        )
        _current_scenario = generate_scenario(cfg)
        D = n_uavs * len(_current_scenario["tasks"])
        print(f"\n[seed={seed}] Scenario: {n_uavs} UAVs, "
              f"{len(_current_scenario['tasks'])} tasks, "
              f"{len(_current_scenario['events'])} events, D={D}")

        for algo_name, algo_kwargs in ALGORITHMS.items():
            print(f"  Running {algo_name}...")
            t0 = time.time()
            np.random.seed(seed)
            use_llm = algo_name in ("DE-LM-always", "TLE", "DE-LM-random")
            llm = (LLMClient(model=llm_model, max_tokens=400, use_cache=True)
                   if use_llm else None)

            if algo_name == "DE":
                algo = DEBaseline(
                    d=D, bounds=(np.zeros(D), np.ones(D)), n_obj=3,
                    pop_size=pop_size, max_gen=max_gen,
                    F=0.5, CR=0.9, strategy="rand", seed=seed,
                )
            elif algo_name == "DE-LM-always":
                algo = StaticLMEABaseline(
                    d=D, bounds=(np.zeros(D), np.ones(D)), n_obj=3,
                    pop_size=pop_size, max_gen=max_gen, llm=llm, seed=seed,
                )
                algo.scheduler_name = "fixed"
                from core.bandit import FixedBudgetScheduler
                algo.scheduler = FixedBudgetScheduler(max_gen // 4, max_gen)
            elif algo_name == "DE-LM-random":
                algo = RandomLMEABaseline(
                    d=D, bounds=(np.zeros(D), np.ones(D)), n_obj=3,
                    pop_size=pop_size, max_gen=max_gen, llm=llm, rate=0.1,
                    seed=seed,
                )
            else:  # TLE
                algo = TLE(
                    d=D, bounds=(np.zeros(D), np.ones(D)), n_obj=3,
                    pop_size=pop_size, max_gen=max_gen, llm=llm,
                    trigger="triple", scheduler="bandit", seed=seed,
                )

            def evaluate(pop):
                NP = pop.shape[0]
                fits = np.zeros((NP, 3))
                for i in range(NP):
                    fits[i] = evaluate_uav_solution(pop[i], _current_scenario)
                return fits

            pop, fit, info = algo.optimize(evaluate)
            elapsed = time.time() - t0

            # Compute metrics
            fronts = fast_non_dominated_sort(fit)
            nd_fit = fit[fronts[0]] if fronts else fit
            # For UAV: objectives are -value, -time, -battery
            # Best = max value, min time, max battery
            f1_value = -np.min(nd_fit[:, 0]) if len(nd_fit) else 0
            f2_time = -np.min(nd_fit[:, 1]) if len(nd_fit) else 600
            f3_battery = -np.max(nd_fit[:, 2]) if len(nd_fit) else 0
            # Ref point
            ref_point = np.array([0, 0, 0])
            try:
                hv = compute_hv(nd_fit - np.array([0, 0, 0]),  # shift to make all positive
                                np.array([f1_value + 1, f2_time + 1, f3_battery + 1]))
            except Exception:
                hv = 0.0

            result = {
                "algo": algo_name,
                "seed": seed,
                "n_uavs": n_uavs,
                "n_tasks": len(_current_scenario["tasks"]),
                "f1_value": float(f1_value),
                "f2_response_time": float(f2_time),
                "f3_battery": float(f3_battery),
                "hv": float(hv),
                "elapsed_sec": float(elapsed),
                "invocations": info.get("invocations", 0),
                "llm_stats": info.get("llm_stats"),
            }
            results.append(result)
            print(f"    -> value={f1_value:.1f}, time={f2_time:.1f}s, "
                  f"battery={f3_battery:.1f}%, invocations={result['invocations']}, "
                  f"elapsed={elapsed:.1f}s")

            # Save intermediate
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--n-uavs", type=int, default=4)
    parser.add_argument("--pop-size", type=int, default=20)
    parser.add_argument("--max-gen", type=int, default=30)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--output", type=str, default=str(RAW_DIR / "exp3_uav.json"))
    args = parser.parse_args()

    print(f"=== UAV Experiment ===")
    print(f"Seeds: {args.seeds}, n_uavs: {args.n_uavs}, "
          f"pop: {args.pop_size}, max_gen: {args.max_gen}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = run_uav_experiment(
        seeds=args.seeds,
        n_uavs=args.n_uavs,
        pop_size=args.pop_size,
        max_gen=args.max_gen,
        llm_model=args.model,
        output_file=args.output,
    )

    print("\n=== UAV Summary ===")
    from collections import defaultdict
    by_algo = defaultdict(list)
    for r in results:
        by_algo[r["algo"]].append((r["f1_value"], r["f2_response_time"],
                                    r["f3_battery"], r["invocations"]))
    for algo, vals in by_algo.items():
        vals = np.array(vals)
        print(f"{algo:25s} | value: {vals[:,0].mean():.1f} ± {vals[:,0].std():.1f} | "
              f"time: {vals[:,1].mean():.1f} ± {vals[:,1].std():.1f}s | "
              f"battery: {vals[:,2].mean():.1f} ± {vals[:,2].std():.1f}% | "
              f"invocations: {vals[:,3].mean():.1f}")
