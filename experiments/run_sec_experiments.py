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
Comprehensive SEC-level experiment:
- 5 algos: DE, DE-LM-static-trigger, PPS-DMOEA, TLE (the new key comparisons)
- 2 problems: DF1, DF5
- 5 seeds
- max_gen=200
- Plus ablation: 4 variants × 2 problems × 3 seeds
"""
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
from baselines.pps_dmoea import PPSDEBaseline


# Main comparison: 4 algorithms (skip DE-LM-always, DE-LM-random which are known to fail)
MAIN_ALGORITHMS = {
    "DE": "DE",
    "DE-LM-static-trigger": "DE-LM-static",
    "PPS-DMOEA": "PPS",
    "TLE": "TLE",
}

# Ablation variants
ABLATION_VARIANTS = {
    "V0_TLE_full": dict(trigger="triple", scheduler="bandit"),
    "V1_single_signal": dict(trigger="single", scheduler="bandit"),
    "V2_heuristic_budget": dict(trigger="triple", scheduler="heuristic"),
    "V3_no_llm": dict(trigger="never", scheduler="bandit"),
}


def run_main(algo_name, problem_name, seed, pop_size, max_gen, d, llm):
    np.random.seed(seed)
    problem = DMOProblem(name=problem_name, d=d, nt=10, taut=10)
    ref_pf = get_reference_pf(problem_name, n=100)

    def evaluate(pop):
        return problem.evaluate(pop)

    if algo_name == "DE":
        algo = DEBaseline(d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
                          pop_size=pop_size, max_gen=max_gen, F=0.5, CR=0.9,
                          strategy="rand", seed=seed)
    elif algo_name == "DE-LM-static-trigger":
        algo = TLE(d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
                   pop_size=pop_size, max_gen=max_gen, llm=llm,
                   trigger="triple", scheduler="heuristic", seed=seed)
    elif algo_name == "PPS-DMOEA":
        algo = PPSDEBaseline(d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
                             pop_size=pop_size, max_gen=max_gen, F=0.5, CR=0.9,
                             seed=seed)
    else:  # TLE
        algo = TLE(d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
                   pop_size=pop_size, max_gen=max_gen, llm=llm,
                   trigger="triple", scheduler="bandit", seed=seed)

    start = time.time()
    pop, fit, info = algo.optimize(evaluate, problem=problem)
    elapsed = time.time() - start

    fronts = fast_non_dominated_sort(fit)
    nd_fit = fit[fronts[0]] if fronts else fit

    try:
        igd = compute_igd(nd_fit, ref_pf)
    except Exception:
        igd = float("inf")
    if problem.M == 2:
        ref_point = np.array([1.1, 1.1])
    else:
        ref_point = np.max(nd_fit, axis=0) * 1.1 + 0.1
    try:
        hv = compute_hv(nd_fit, ref_point)
    except Exception:
        hv = 0.0

    return {
        "algo": algo_name, "problem": problem_name, "seed": seed,
        "max_gen": max_gen, "pop_size": pop_size,
        "igd": float(igd), "hv": float(hv),
        "elapsed_sec": elapsed,
        "invocations": info.get("invocations", 0),
        "best_fitness_history": info.get("best_fitness_history", []),
        "trigger_stats": info.get("trigger_stats"),
        "scheduler_stats": info.get("scheduler_stats"),
    }


def run_ablation(variant_name, variant_kwargs, problem_name, seed, pop_size, max_gen, d, llm):
    np.random.seed(seed)
    problem = DMOProblem(name=problem_name, d=d, nt=10, taut=10)
    ref_pf = get_reference_pf(problem_name, n=100)

    def evaluate(pop):
        return problem.evaluate(pop)

    if variant_name == "V3_no_llm":
        # Pure DE
        algo = DEBaseline(d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
                          pop_size=pop_size, max_gen=max_gen, F=0.5, CR=0.9,
                          strategy="rand", seed=seed)
    else:
        algo = TLE(d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
                   pop_size=pop_size, max_gen=max_gen, llm=llm,
                   trigger=variant_kwargs["trigger"],
                   scheduler=variant_kwargs["scheduler"],
                   seed=seed)

    start = time.time()
    pop, fit, info = algo.optimize(evaluate, problem=problem)
    elapsed = time.time() - start

    fronts = fast_non_dominated_sort(fit)
    nd_fit = fit[fronts[0]] if fronts else fit

    try:
        igd = compute_igd(nd_fit, ref_pf)
    except Exception:
        igd = float("inf")

    return {
        "variant": variant_name, "problem": problem_name, "seed": seed,
        "igd": float(igd), "elapsed_sec": elapsed,
        "invocations": info.get("invocations", 0),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["main", "ablation"], required=True)
    parser.add_argument("--problems", nargs="+", default=["DF1", "DF5"])
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2, 3, 4])
    parser.add_argument("--pop-size", type=int, default=50)
    parser.add_argument("--max-gen", type=int, default=200)
    parser.add_argument("--d", type=int, default=10)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    print(f"=== Mode: {args.mode} ===")
    print(f"Problems: {args.problems}, Seeds: {args.seeds}, max_gen: {args.max_gen}")
    print(f"Output: {args.output}")
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
    print()

    llm = LLMClient(model=args.model, max_tokens=400, use_cache=True)
    results = []

    if args.mode == "main":
        # Skip DE-LM-always and DE-LM-random (known to fail)
        algos = ["DE", "DE-LM-static-trigger", "PPS-DMOEA", "TLE"]
        total = len(algos) * len(args.problems) * len(args.seeds)
        idx = 0
        start_total = time.time()
        for problem in args.problems:
            for algo in algos:
                for seed in args.seeds:
                    idx += 1
                    print(f"[{idx}/{total}] {algo:25s} {problem:5s} seed={seed}", end=" ... ")
                    try:
                        r = run_main(algo, problem, seed, args.pop_size, args.max_gen, args.d, llm)
                        results.append(r)
                        elapsed = time.time() - start_total
                        eta = (elapsed / idx) * (total - idx)
                        print(f"IGD={r['igd']:.4f} inv={r['invocations']} t={r['elapsed_sec']:.0f}s ETA={eta/60:.1f}m")
                    except Exception as e:
                        print(f"ERROR: {e}")
                        results.append({"algo": algo, "problem": problem, "seed": seed, "error": str(e)})
                    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
                    with open(args.output, "w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)

    else:  # ablation
        variants = list(ABLATION_VARIANTS.keys())
        total = len(variants) * len(args.problems) * len(args.seeds)
        idx = 0
        start_total = time.time()
        for problem in args.problems:
            for variant in variants:
                variant_kwargs = ABLATION_VARIANTS[variant]
                for seed in args.seeds:
                    idx += 1
                    print(f"[{idx}/{total}] {variant:20s} {problem:5s} seed={seed}", end=" ... ")
                    try:
                        r = run_ablation(variant, variant_kwargs, problem, seed, args.pop_size, args.max_gen, args.d, llm)
                        results.append(r)
                        elapsed = time.time() - start_total
                        eta = (elapsed / idx) * (total - idx)
                        print(f"IGD={r['igd']:.4f} inv={r['invocations']} t={r['elapsed_sec']:.0f}s ETA={eta/60:.1f}m")
                    except Exception as e:
                        print(f"ERROR: {e}")
                        results.append({"variant": variant, "problem": problem, "seed": seed, "error": str(e)})
                    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
                    with open(args.output, "w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)

    total_min = (time.time() - start_total) / 60
    print(f"\n=== Done: {total_min:.1f} min ===")


if __name__ == "__main__":
    main()
