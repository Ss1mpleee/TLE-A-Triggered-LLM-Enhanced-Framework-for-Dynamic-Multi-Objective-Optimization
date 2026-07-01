"""
Long-Budget Experiment: Verify TLE's advantage at max_gen=200+ with multiple seeds.

This is the CRITICAL experiment to validate TLE's "selling point":
- If TLE > DE / DE-LM-static at max_gen=200, the paper is viable
- If TLE still ~ DE, we need to reconsider the approach

Configuration:
- max_gen = 200 (vs 60 in short-budget)
- 3 seeds
- 3 algorithms (DE, DE-LM-static-trigger, TLE) — skip DE-LM-always (known to fail)
- 2 problems: DF1, DF5
- Total: 3 algos × 2 problems × 3 seeds = 18 runs
"""
import sys
sys.path.insert(0, "D:/新论文/实验")

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
    DEFAULT_MODEL,
)
from benchmarks import DMOProblem, get_reference_pf
from core.moo_utils import compute_igd, compute_hv, fast_non_dominated_sort


ALGORITHMS = {
    "DE": dict(trigger="never", scheduler="bandit"),
    "DE-LM-static-trigger": dict(trigger="triple", scheduler="heuristic"),
    "TLE": dict(trigger="triple", scheduler="bandit"),
}


def run_single(algo_name, algo_kwargs, problem_name, seed, pop_size, max_gen, d, llm):
    np.random.seed(seed)
    problem = DMOProblem(name=problem_name, d=d, nt=10, taut=10)
    ref_pf = get_reference_pf(problem_name, n=100)

    def evaluate(pop):
        return problem.evaluate(pop)

    if algo_name == "DE":
        algo = DEBaseline(
            d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
            pop_size=pop_size, max_gen=max_gen,
            F=0.5, CR=0.9, strategy="rand", seed=seed,
        )
    elif algo_name == "DE-LM-static-trigger":
        algo = TLE(
            d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
            pop_size=pop_size, max_gen=max_gen, llm=llm,
            trigger="triple", scheduler="heuristic", seed=seed,
        )
    else:  # TLE
        algo = TLE(
            d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
            pop_size=pop_size, max_gen=max_gen, llm=llm,
            trigger="triple", scheduler="bandit", seed=seed,
        )

    start_time = time.time()
    pop, fit, info = algo.optimize(evaluate, problem=problem)
    elapsed = time.time() - start_time

    # Compute final IGD/HV
    fronts = fast_non_dominated_sort(fit)
    nd_fit = fit[fronts[0]] if fronts else fit

    # IGD per gen (key metric for showing convergence)
    igd_history = []
    history = info.get("best_fitness_history", [])
    # Compute IGD only at the end (efficient)
    try:
        igd_final = compute_igd(nd_fit, ref_pf)
    except Exception:
        igd_final = float("inf")

    # HV
    if problem.M == 2:
        ref_point = np.array([1.1, 1.1])
    else:
        ref_point = np.max(nd_fit, axis=0) * 1.1 + 0.1
    try:
        hv = compute_hv(nd_fit, ref_point)
    except Exception:
        hv = 0.0

    # Per-step IGD via time-varying detection
    # Simulate change steps: for t=0, 10, 20, ..., 200
    change_igds = []
    # We don't have time-series IGD; just record final IGD
    # (For a full analysis we'd need to capture IGD at each change step)

    return {
        "algo": algo_name,
        "problem": problem_name,
        "seed": seed,
        "max_gen": max_gen,
        "pop_size": pop_size,
        "igd_final": float(igd_final),
        "hv": float(hv),
        "elapsed_sec": float(elapsed),
        "invocations": info.get("invocations", 0),
        "best_fitness_history": info.get("best_fitness_history", []),
        "trigger_stats": info.get("trigger_stats"),
        "scheduler_stats": info.get("scheduler_stats"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--problems", nargs="+", default=["DF1", "DF5"])
    parser.add_argument("--algorithms", nargs="+", default=list(ALGORITHMS.keys()))
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--pop-size", type=int, default=50)
    parser.add_argument("--max-gen", type=int, default=200)
    parser.add_argument("--d", type=int, default=10)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--output", type=str,
                        default="实验/results/raw/exp_long_budget.json")
    args = parser.parse_args()

    print(f"=== TLE Long-Budget Validation Experiment ===")
    print(f"Problems: {args.problems}")
    print(f"Algorithms: {args.algorithms}")
    print(f"Seeds: {args.seeds}")
    print(f"Pop: {args.pop_size}, Max gen: {args.max_gen}, D: {args.d}")
    print(f"Model: {args.model}")
    print(f"Output: {args.output}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    llm = LLMClient(model=args.model, max_tokens=400, use_cache=True)
    results = []
    total_runs = len(args.problems) * len(args.algorithms) * len(args.seeds)
    run_idx = 0
    start_total = time.time()

    for problem in args.problems:
        for algo_name in args.algorithms:
            algo_kwargs = ALGORITHMS[algo_name]
            for seed in args.seeds:
                run_idx += 1
                print(f"[{run_idx}/{total_runs}] "
                      f"algo={algo_name:25s} problem={problem:5s} seed={seed}", end=" ... ")
                try:
                    result = run_single(
                        algo_name=algo_name,
                        algo_kwargs=algo_kwargs,
                        problem_name=problem,
                        seed=seed,
                        pop_size=args.pop_size,
                        max_gen=args.max_gen,
                        d=args.d,
                        llm=llm,
                    )
                    results.append(result)
                    elapsed_so_far = time.time() - start_total
                    eta = (elapsed_so_far / run_idx) * (total_runs - run_idx)
                    print(f"IGD={result['igd_final']:.4f}, "
                          f"invocations={result['invocations']}, "
                          f"time={result['elapsed_sec']:.0f}s, "
                          f"ETA={eta/60:.1f}min")
                except Exception as e:
                    print(f"ERROR: {e}")
                    import traceback; traceback.print_exc()
                    results.append({
                        "algo": algo_name, "problem": problem, "seed": seed,
                        "error": str(e),
                    })

                # Save intermediate
                Path(args.output).parent.mkdir(parents=True, exist_ok=True)
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

    total_elapsed = time.time() - start_total
    print(f"\n=== Total time: {total_elapsed/60:.1f} min ===")

    # Summary
    print("\n=== Long-Budget Summary ===")
    by_ap = defaultdict(list)
    for r in results:
        if "error" not in r:
            by_ap[(r["algo"], r["problem"])].append((r["igd_final"], r["hv"], r["invocations"]))

    # Print as table
    problems_list = sorted(set(r["problem"] for r in results if "problem" in r))
    algos_list = args.algorithms

    print(f"\n{'Algorithm':25s} | ", end="")
    for p in problems_list:
        print(f"{p:30s} | ", end="")
    print()

    for algo in algos_list:
        print(f"{algo:25s} | ", end="")
        for p in problems_list:
            vals = by_ap.get((algo, p), [])
            if vals:
                igds = [v[0] for v in vals]
                invs = [v[2] for v in vals]
                print(f"IGD={np.mean(igds):.4f}±{np.std(igds):.4f} | inv={np.mean(invs):.1f} | ", end="")
            else:
                print(f"{'N/A':30s} | ", end="")
        print()

    # Critical analysis: does TLE beat DE-LM-static?
    print("\n=== Critical Analysis: TLE vs DE-LM-static-trigger ===")
    for p in problems_list:
        tle_vals = [v[0] for v in by_ap.get(("TLE", p), [])]
        static_vals = [v[0] for v in by_ap.get(("DE-LM-static-trigger", p), [])]
        de_vals = [v[0] for v in by_ap.get(("DE", p), [])]
        if tle_vals and static_vals:
            tle_mean = np.mean(tle_vals)
            static_mean = np.mean(static_vals)
            de_mean = np.mean(de_vals)
            print(f"  {p}: DE={de_mean:.4f} | Static={static_mean:.4f} | TLE={tle_mean:.4f} | "
                  f"TLE improvement over DE: {(de_mean-tle_mean)/de_mean*100:+.1f}% | "
                  f"TLE improvement over Static: {(static_mean-tle_mean)/static_mean*100:+.1f}%")


if __name__ == "__main__":
    main()
