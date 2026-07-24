"""
Comprehensive smoke test: TLE-MA vs DE vs DNSGA-II-A on DF1/DF5/DF7.
5 seeds each, 100 generations.

Goal: verify TLE-MA is competitive before scaling up to 30 seeds full experiment.
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
    """For minimization, lower is better. Use sum of objectives."""
    return float(np.min(np.sum(fit, axis=1)))


def main():
    model = "qwen2.5:7b"
    print(f"=== TLE-MA comprehensive smoke test (model={model}) ===")
    print("Problems: DF1, DF5, DF7 (3 medium-difficulty DMO)")
    print("Algos: DE / DNSGA-II-A / TLE-MA")
    print("Seeds: 5 (0-4), Generations: 100, Pop: 100, Dim: 10")
    print()

    llm = LLMClient(model=model, temperature=0.0)

    results = {}  # {(problem, algo): [best_per_seed]}
    action_distributions = {}  # {problem: [actions_per_seed]}

    for problem_name in ["DF1", "DF5", "DF7"]:
        print(f"\n=== {problem_name} ===")
        for algo_name, algo_cls in [("DE", DEBaseline), ("DNSGA-II-A", DNSGAIIA), ("TLE-MA", TLEMultiAction)]:
            print(f"  -- {algo_name} --")
            seeds_bests = []
            for seed in [0, 1, 2, 3, 4]:
                t0 = time.time()
                if algo_cls is TLEMultiAction:
                    _, fit, info = run_one(
                        TLEMultiAction, problem_name, seed, llm=llm,
                        trigger="triple", scheduler="heuristic",
                    )
                    if problem_name not in action_distributions:
                        action_distributions[problem_name] = []
                    action_distributions[problem_name].append(info["action_distribution"])
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
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"{'Problem':<8} {'DE':>16} {'DNSGA-II-A':>16} {'TLE-MA':>16} {'TLE-MA vs DE':>14} {'vs DNSGA':>10}")
    print("-" * 70)
    for problem_name in ["DF1", "DF5", "DF7"]:
        de_mean = np.mean(results[(problem_name, "DE")])
        dnsga_mean = np.mean(results[(problem_name, "DNSGA-II-A")])
        tlema_mean = np.mean(results[(problem_name, "TLE-MA")])
        tlema_vs_de = (tlema_mean - de_mean) / de_mean * 100
        tlema_vs_dnsga = (tlema_mean - dnsga_mean) / dnsga_mean * 100
        print(f"{problem_name:<8} {de_mean:>8.4f}+/-{np.std(results[(problem_name,'DE')]):.3f}  "
              f"{dnsga_mean:>8.4f}+/-{np.std(results[(problem_name,'DNSGA-II-A')]):.3f}  "
              f"{tlema_mean:>8.4f}+/-{np.std(results[(problem_name,'TLE-MA')]):.3f}  "
              f"{tlema_vs_de:>+10.2f}%  {tlema_vs_dnsga:>+7.2f}%")

    print()
    print("Action distributions by problem (qwen2.5:7b):")
    from collections import Counter
    for problem_name in ["DF1", "DF5", "DF7"]:
        merged = Counter()
        for d in action_distributions.get(problem_name, []):
            merged.update(d)
        total = sum(merged.values())
        if total == 0:
            continue
        print(f"  {problem_name} (total {total}):")
        for k in ["param", "archive_reset", "restart_top", "diversity_injection"]:
            c = merged.get(k, 0)
            pct = 100 * c / total
            print(f"    {k}: {c} ({pct:.1f}%)")


if __name__ == "__main__":
    main()