"""
UAV experiment: 30-seed run for SWEVO submission.
Run all 5 algorithms (DE, DE-LM-static-trigger, PPS-DMOEA, DNSGA-II-A, TLE)
on both 4-UAV and 8-UAV scenarios with n=30 seeds each.

Uses the existing exp3_uav_v2.json as the "first 5 seeds" baseline and appends
seeds 5..29 to it. Saves intermediate progress to exp3_uav_v3.json.

Estimated time:
- TLE (LLM): ~120-180s/run × 60 runs = 2-3 hours
- DE/Static/PPS/DNSGA: ~35-80s/run × 240 runs = 2.5-5 hours
- Total: 5-8 hours (mostly cache misses for new seeds)

Usage:
  python run_uav_30seeds.py [--algos TLE DE ...] [--seeds 5..29] [--n-uavs 4 8]
"""
import sys
sys.path.insert(0, r'D:\新论文\实验')

import json
import time
import argparse
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from core import (
    LLMClient, TLE, DEBaseline,
    StaticLMEABaseline, RandomLMEABaseline,
    PPSDMOEA, DNSGAIIA,
    DEFAULT_MODEL,
)
from benchmarks.uav_scenario import ScenarioConfig, generate_scenario, evaluate_uav_solution
from core.moo_utils import fast_non_dominated_sort, compute_hv


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


def run_algo(algo_name, D, scenario, pop_size, max_gen, llm_model, seed):
    """Run a single algorithm on a scenario, return results dict."""
    np.random.seed(seed)

    use_llm = algo_name in ("DE-LM-static-trigger", "TLE")
    llm = (LLMClient(model=llm_model, max_tokens=400, use_cache=True)
           if use_llm else None)

    bounds = (np.zeros(D), np.ones(D))

    if algo_name == "DE":
        algo = DEBaseline(
            d=D, bounds=bounds, n_obj=3,
            pop_size=pop_size, max_gen=max_gen,
            F=0.5, CR=0.9, strategy="rand", seed=seed,
        )
    elif algo_name == "DE-LM-static-trigger":
        algo = StaticLMEABaseline(
            d=D, bounds=bounds, n_obj=3,
            pop_size=pop_size, max_gen=max_gen, llm=llm, seed=seed,
        )
        algo.scheduler_name = "fixed"
        from core.bandit import FixedBudgetScheduler
        algo.scheduler = FixedBudgetScheduler(max_gen // 4, max_gen)
    elif algo_name == "PPS-DMOEA":
        algo = PPSDMOEA(
            d=D, bounds=bounds, n_obj=3,
            pop_size=pop_size, max_gen=max_gen, seed=seed,
        )
    elif algo_name == "DNSGA-II-A":
        algo = DNSGAIIA(
            d=D, bounds=bounds, n_obj=3,
            pop_size=pop_size, max_gen=max_gen, seed=seed,
        )
    elif algo_name == "TLE":
        algo = TLE(
            d=D, bounds=bounds, n_obj=3,
            pop_size=pop_size, max_gen=max_gen, llm=llm,
            trigger="triple", scheduler="bandit", seed=seed,
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
    ref_point = np.array([f1_value + 1, f2_time + 1, f3_battery + 1])
    try:
        shifted = nd_fit - np.array([0, 0, 0])
        hv = compute_hv(shifted, ref_point)
    except Exception:
        hv = 0.0

    return {
        "algo": algo_name,
        "seed": seed,
        "n_uavs": scenario.get("n_uavs", 0),
        "n_tasks": len(scenario["tasks"]),
        "f1_value": float(f1_value),
        "f2_response_time": float(f2_time),
        "f3_battery": float(f3_battery),
        "hv": float(hv),
        "elapsed_sec": float(elapsed),
        "invocations": info.get("invocations", 0),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--algos", nargs="+",
                        default=["DE", "DE-LM-static-trigger", "PPS-DMOEA", "DNSGA-II-A", "TLE"])
    parser.add_argument("--n-uavs", nargs="+", type=int, default=[4, 8])
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(5, 30)))
    parser.add_argument("--pop-size", type=int, default=30)
    parser.add_argument("--max-gen", type=int, default=40)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--input", type=str,
                        default=r"D:\新论文\实验\results\raw\exp3_uav_v2.json",
                        help="Seed data file (existing n=5 data)")
    parser.add_argument("--output", type=str,
                        default=r"D:\新论文\实验\results\raw\exp3_uav_v3.json")
    args = parser.parse_args()

    # Load existing data
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    if Path(args.output).exists():
        all_results = json.load(open(args.output, encoding='utf-8'))
        print(f"[load] Loaded {len(all_results)} existing results from {args.output}")
    elif Path(args.input).exists():
        all_results = json.load(open(args.input, encoding='utf-8'))
        print(f"[seed] Loaded {len(all_results)} seed results from {args.input}")
    else:
        all_results = []
        print(f"[new] Starting fresh")

    # Track which (algo, n_uavs, seed) tuples are already done
    done_keys = {(r['algo'], r['n_uavs'], r['seed']) for r in all_results}
    print(f"[skip] Already have {len(done_keys)} (algo,n_uavs,seed) tuples")

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
        # Build scenario (same as existing 5-seed data)
        cfg = ScenarioConfig(
            n_uavs=nu,
            simulation_time=300.0,
            task_arrival_rate=0.3,
            seed=seed,
        )
        scenario = generate_scenario(cfg)
        scenario["n_uavs"] = nu
        D = nu * len(scenario["tasks"])

        print(f"[{i}/{len(pending)}] {algo:25s} n_uavs={nu} seed={seed} D={D}")
        t0 = time.time()
        try:
            result = run_algo(algo, D, scenario, args.pop_size, args.max_gen, args.model, seed)
            elapsed = time.time() - t0
            print(f"  -> value={result['f1_value']:.1f}, "
                  f"time={result['f2_response_time']:.1f}s, "
                  f"inv={result['invocations']}, "
                  f"took {elapsed:.1f}s")
            all_results.append(result)

            # Save incremental
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            continue

        # ETA
        elapsed_total = time.time() - t_start
        avg_per_run = elapsed_total / i
        eta = avg_per_run * (len(pending) - i)
        print(f"  total elapsed: {elapsed_total/60:.1f}m, ETA: {eta/60:.1f}m")

    print(f"\n=== Done: {len(pending)} runs in {(time.time()-t_start)/3600:.2f}h ===")
    print(f"Output: {args.output} ({len(all_results)} total records)")


if __name__ == "__main__":
    main()