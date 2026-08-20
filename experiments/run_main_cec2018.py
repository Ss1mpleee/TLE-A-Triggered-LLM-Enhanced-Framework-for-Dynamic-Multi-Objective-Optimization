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
Main Experiment Script: TLE vs Baselines on CEC2018 Dynamic Multi-Objective
==========================================================================
Runs all baselines + TLE on multiple CEC2018 problems and saves results to JSON.
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
    PPSDMOEA, DNSGAIIA,
    DEFAULT_MODEL,
)
from baselines.moea_dd import MOEADD
from benchmarks import DMOProblem, get_reference_pf
from core.moo_utils import compute_igd, compute_hv, fast_non_dominated_sort


# ============ Configurations ============
# Stage-1 revision: complete CEC 2018 coverage — all 14 problems
# (DF1-DF14), including the 3-objective problems DF9-DF14.
PROBLEMS_2OBJ = ["DF1", "DF2", "DF3", "DF4", "DF5", "DF6", "DF7", "DF8"]
PROBLEMS_3OBJ = ["DF9", "DF10", "DF11", "DF12", "DF13", "DF14"]
ALL_PROBLEMS = PROBLEMS_2OBJ + PROBLEMS_3OBJ

# All six algorithms.  Note: each algo_name below is matched in the
# run_single dispatch below; ALGORITHMS is now only used for LLM-using
# variants (TLE / static-trigger) to pick their trigger/scheduler combo.
ALGORITHM_NAMES = [
    "DE", "DE-LM-static-trigger", "TLE",
    "PPS-DMOEA", "DNSGA-II-A", "MOEA/DD",
]

# All algorithm names MUST be in ALGORITHMS dict as keys (even if value
# is unused) because the dispatch in run_experiment_set indexes into it.
ALGORITHMS = {
    "DE": dict(trigger="never", scheduler="bandit"),
    "DE-LM-always": dict(trigger="always", scheduler="fixed"),
    "DE-LM-random": dict(trigger="random", scheduler="fixed"),
    "DE-LM-static-trigger": dict(trigger="triple", scheduler="heuristic"),
    "TLE": dict(trigger="triple", scheduler="bandit"),
    "PPS-DMOEA": dict(),  # not used; dispatch handles via algo_name
    "DNSGA-II-A": dict(),
    "MOEA/DD": dict(),
}


def run_single(
    algo_name: str,
    algo_kwargs: dict,
    problem_name: str,
    seed: int,
    pop_size: int = 50,
    max_gen: int = 100,
    d: int = 10,
    use_llm: bool = True,
    llm_model: str = DEFAULT_MODEL,
) -> dict:
    """Run a single (algorithm, problem, seed) configuration."""
    np.random.seed(seed)

    # Build problem
    problem = DMOProblem(name=problem_name, d=d, nt=10, taut=10)
    ref_pf = get_reference_pf(problem_name, n=100)

    def evaluate(pop):
        return problem.evaluate(pop)

    # Build LLM client (shared via cache)
    llm = None
    if use_llm and algo_kwargs.get("trigger") in ("triple", "always"):
        llm = LLMClient(model=llm_model, max_tokens=500, use_cache=True)

    # Select algorithm
    if algo_name == "DE":
        algo = DEBaseline(
            d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
            pop_size=pop_size, max_gen=max_gen,
            F=0.5, CR=0.9, strategy="rand", seed=seed,
        )
    elif algo_name == "DE-LM-always":
        # Cap LLM calls to avoid blowing up runtime
        budget = max(5, max_gen // 4)
        algo = StaticLMEABaseline(
            d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
            pop_size=pop_size, max_gen=max_gen, llm=llm, seed=seed,
        )
        # Force fixed budget
        algo.scheduler_name = "fixed"
        from core.bandit import FixedBudgetScheduler
        algo.scheduler = FixedBudgetScheduler(budget, max_gen)
    elif algo_name == "DE-LM-random":
        algo = RandomLMEABaseline(
            d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
            pop_size=pop_size, max_gen=max_gen, llm=llm, rate=0.1, seed=seed,
        )
    elif algo_name == "PPS-DMOEA":
        algo = PPSDMOEA(
            d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
            pop_size=pop_size, max_gen=max_gen, seed=seed,
        )
    elif algo_name == "DNSGA-II-A":
        algo = DNSGAIIA(
            d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
            pop_size=pop_size, max_gen=max_gen, seed=seed,
        )
    elif algo_name == "MOEA/DD":
        algo = MOEADD(
            d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
            pop_size=pop_size, max_gen=max_gen, seed=seed,
        )
    else:
        # TLE variants
        algo = TLE(
            d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
            pop_size=pop_size, max_gen=max_gen, llm=llm,
            trigger=algo_kwargs.get("trigger", "triple"),
            scheduler=algo_kwargs.get("scheduler", "bandit"),
            seed=seed,
        )

    # Run
    start_time = time.time()
    pop, fit, info = algo.optimize(evaluate, problem=problem)
    elapsed = time.time() - start_time

    # Compute final IGD and HV
    # Filter non-dominated
    fronts = fast_non_dominated_sort(fit)
    nd_pop = pop[fronts[0]] if fronts else pop
    nd_fit = fit[fronts[0]] if fronts else fit

    # Clip negative values for HV reference
    ref_point = np.max(nd_fit, axis=0) * 1.1 + 0.1
    if problem.M == 2:
        ref_point = np.array([1.1, 1.1])

    try:
        igd = compute_igd(nd_fit, ref_pf)
    except Exception:
        igd = float("inf")
    try:
        hv = compute_hv(nd_fit, ref_point)
    except Exception:
        hv = 0.0

    return {
        "algo": algo_name,
        "problem": problem_name,
        "seed": seed,
        "igd": float(igd),
        "hv": float(hv),
        "elapsed_sec": float(elapsed),
        "invocations": info.get("invocations", 0),
        "best_fitness_history": info.get("best_fitness_history", []),
        "llm_stats": info.get("llm_stats"),
        "trigger_stats": info.get("trigger_stats"),
        "scheduler_stats": info.get("scheduler_stats"),
    }


def run_experiment_set(
    problems: list,
    algorithms: list,
    seeds: list,
    pop_size: int = 50,
    max_gen: int = 100,
    d: int = 10,
    output_file: str = None,
):
    """Run full experiment set and save to JSON."""
    # Resume support: load existing results if file exists and skip done runs
    results = []
    done_keys = set()
    if output_file and Path(output_file).exists():
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                results = json.load(f)
            for r in results:
                if "error" not in r and "algo" in r and "problem" in r and "seed" in r:
                    done_keys.add((r["algo"], r["problem"], r["seed"]))
            print(f"[Resume] Loaded {len(results)} existing runs from {output_file}, "
                  f"{len(done_keys)} successful keys will be skipped.")
        except Exception as e:
            print(f"[Resume] Could not load existing {output_file}: {e}")
            results = []

    total_runs = len(problems) * len(algorithms) * len(seeds)
    run_idx = 0
    skipped = 0

    for problem in problems:
        for algo_name in algorithms:
            algo_kwargs = ALGORITHMS[algo_name]
            for seed in seeds:
                run_idx += 1
                key = (algo_name, problem, seed)
                if key in done_keys:
                    skipped += 1
                    if run_idx % 30 == 0 or run_idx == total_runs:
                        print(f"[{run_idx}/{total_runs}] "
                              f"SKIP (already done) algo={algo_name:25s} "
                              f"problem={problem:5s} seed={seed}  [total skipped: {skipped}]")
                    continue
                print(f"[{run_idx}/{total_runs}] "
                      f"algo={algo_name:25s} problem={problem:5s} seed={seed}")
                try:
                    result = run_single(
                        algo_name=algo_name,
                        algo_kwargs=algo_kwargs,
                        problem_name=problem,
                        seed=seed,
                        pop_size=pop_size,
                        max_gen=max_gen,
                        d=d,
                    )
                    results.append(result)
                    done_keys.add(key)
                    print(f"  -> IGD={result['igd']:.4f}, HV={result['hv']:.4f}, "
                          f"invocations={result['invocations']}, "
                          f"elapsed={result['elapsed_sec']:.1f}s")
                except Exception as e:
                    print(f"  -> ERROR: {e}")
                    results.append({
                        "algo": algo_name,
                        "problem": problem,
                        "seed": seed,
                        "error": str(e),
                    })

                # Save intermediate
                if output_file:
                    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)

    if skipped > 0:
        print(f"[Done] Skipped {skipped} already-completed runs, "
              f"wrote {len(results)} total results to {output_file}")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--problems", nargs="+", default=ALL_PROBLEMS)
    parser.add_argument("--algorithms", nargs="+", default=list(ALGORITHMS.keys()))
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(30)))
    parser.add_argument("--pop-size", type=int, default=50)
    parser.add_argument("--max-gen", type=int, default=100)
    parser.add_argument("--d", type=int, default=10)
    parser.add_argument("--output", type=str,
                        default=str(RAW_DIR / "exp2_dynamic_mo.json"))
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    args = parser.parse_args()

    print(f"=== TLE Main Experiment ===")
    print(f"Problems: {args.problems}")
    print(f"Algorithms: {args.algorithms}")
    print(f"Seeds: {args.seeds}")
    print(f"Pop size: {args.pop_size}, Max gen: {args.max_gen}, D: {args.d}")
    print(f"Output: {args.output}")
    print(f"LLM model: {args.model}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = run_experiment_set(
        problems=args.problems,
        algorithms=args.algorithms,
        seeds=args.seeds,
        pop_size=args.pop_size,
        max_gen=args.max_gen,
        d=args.d,
        output_file=args.output,
    )

    print()
    print("=== Summary ===")
    # Aggregate by (algo, problem)
    from collections import defaultdict
    by_ap = defaultdict(list)
    for r in results:
        if "error" not in r:
            by_ap[(r["algo"], r["problem"])].append((r["igd"], r["hv"]))

    for (algo, prob), vals in sorted(by_ap.items()):
        igds = [v[0] for v in vals]
        hvs = [v[1] for v in vals]
        print(f"{algo:25s} | {prob:5s} | IGD: {np.mean(igds):.4f} ± {np.std(igds):.4f} | "
              f"HV: {np.mean(hvs):.4f} ± {np.std(hvs):.4f}")


if __name__ == "__main__":
    main()
