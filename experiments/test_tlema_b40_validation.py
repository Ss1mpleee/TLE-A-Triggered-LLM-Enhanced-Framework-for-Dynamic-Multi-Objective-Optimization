"""
Validate budget=40 finding across DF1, DF5, DF7.
Also compare against DNSGA-II-A.
"""
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\新论文\实验")
sys.path.insert(0, str(ROOT))

import numpy as np
from core.tle import TLEMultiAction, DEBaseline, DNSGAIIA
from core.llm_interface import LLMClient
from benchmarks.cec2018 import DMOProblem


def run_one(algo_cls, problem_name, seed, llm=None, max_gen=100, **algo_kwargs):
    problem = DMOProblem(name=problem_name, d=10, nt=10, taut=10)
    if algo_cls is DEBaseline:
        algo = algo_cls(
            d=10, bounds=(problem.lower, problem.upper), n_obj=problem.M,
            pop_size=100, max_gen=max_gen, seed=seed, **algo_kwargs,
        )
    elif algo_cls is DNSGAIIA:
        algo = algo_cls(
            d=10, bounds=(problem.lower, problem.upper), n_obj=problem.M,
            pop_size=100, max_gen=max_gen, seed=seed, **algo_kwargs,
        )
    else:
        algo = algo_cls(
            d=10, bounds=(problem.lower, problem.upper), n_obj=problem.M,
            pop_size=100, max_gen=max_gen, llm=llm, seed=seed, **algo_kwargs,
        )
    pop, fit, info = algo.optimize(problem.evaluate, problem=problem)
    return pop, fit, info


def best_fitness(fit):
    return float(np.min(np.sum(fit, axis=1)))


def main():
    model = "qwen2.5:7b"
    print(f"=== TLE-MA budget=40 validation across problems ===")
    print()

    llm = LLMClient(model=model, temperature=0.0)

    seeds = [0, 1, 2, 3, 4]
    problems = ["DF1", "DF5", "DF7"]

    # Run all configs
    results = {}
    for problem_name in problems:
        print(f"\n=== {problem_name} ===")
        for algo_name, algo_cls, kwargs in [
            ("DE", DEBaseline, {}),
            ("DNSGA-II-A", DNSGAIIA, {}),
            ("TLE-MA(b=20)", TLEMultiAction, {"budget": 20, "scheduler": "fixed"}),
            ("TLE-MA(b=40)", TLEMultiAction, {"budget": 40, "scheduler": "fixed"}),
            ("TLE-MA(b=80)", TLEMultiAction, {"budget": 80, "scheduler": "fixed"}),
        ]:
            print(f"  -- {algo_name} --")
            seeds_bests = []
            for seed in seeds:
                t0 = time.time()
                if algo_cls is TLEMultiAction:
                    _, fit, info = run_one(
                        TLEMultiAction, problem_name, seed, llm=llm, **kwargs,
                    )
                else:
                    _, fit, info = run_one(algo_cls, problem_name, seed)
                best = best_fitness(fit)
                seeds_bests.append(best)
                elapsed = time.time() - t0
                print(f"    seed {seed}: best={best:.4f} ({elapsed:.1f}s)")
            results[(problem_name, algo_name)] = seeds_bests
            mean = np.mean(seeds_bests)
            std = np.std(seeds_bests)
            print(f"  {algo_name} avg: {mean:.4f} +/- {std:.4f}")

    # Summary
    print()
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"{'Problem':<8} {'DE':>14} {'DNSGA-II-A':>14} {'TLE-MA(20)':>14} {'TLE-MA(40)':>14} {'TLE-MA(80)':>14}")
    print("-" * 80)
    for problem_name in problems:
        row = f"{problem_name:<8}"
        for algo_name in ["DE", "DNSGA-II-A", "TLE-MA(b=20)", "TLE-MA(b=40)", "TLE-MA(b=80)"]:
            v = np.mean(results[(problem_name, algo_name)])
            s = np.std(results[(problem_name, algo_name)])
            row += f"  {v:>6.4f}+/-{s:.3f}"
        print(row)
    print()
    print("TLE-MA(40) vs DE / DNSGA-II-A (lower is better):")
    for problem_name in problems:
        de = np.mean(results[(problem_name, "DE")])
        dnsga = np.mean(results[(problem_name, "DNSGA-II-A")])
        tlema40 = np.mean(results[(problem_name, "TLE-MA(b=40)")])
        print(f"  {problem_name}: TLE-MA(40) vs DE = {(tlema40-de)/de*100:+.2f}%, "
              f"vs DNSGA = {(tlema40-dnsga)/dnsga*100:+.2f}%")


if __name__ == "__main__":
    main()