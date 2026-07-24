"""
Test if TLE-MA hurts because of LLM interference frequency.
Compare TLE-MA at different LLM trigger rates.
Hypothesis: if LLM is too disruptive, fewer LLM calls = better results.
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
    print(f"=== TLE-MA frequency sensitivity test ===")
    print("Hypothesis: lower LLM rate -> less interference -> better DE-like behavior")
    print()

    llm = LLMClient(model=model, temperature=0.0)

    # Test on DF5 (most stable)
    problem_name = "DF5"
    seeds = [0, 1, 2, 3, 4]

    # DE baseline (no LLM)
    de_bests = []
    for seed in seeds:
        _, fit, _ = run_one(DEBaseline, problem_name, seed)
        de_bests.append(best_fitness(fit))
    print(f"DE (no LLM): avg={np.mean(de_bests):.4f}")

    # DNSGA-II-A baseline
    dnsga_bests = []
    for seed in seeds:
        _, fit, _ = run_one(DNSGAIIA, problem_name, seed)
        dnsga_bests.append(best_fitness(fit))
    print(f"DNSGA-II-A:  avg={np.mean(dnsga_bests):.4f}")

    # TLE-MA with different scheduler budgets (lower budget = less LLM)
    # scheduler="fixed" with budget=X means max X LLM calls per run
    for budget in [5, 10, 20, 40, 80]:
        tlema_bests = []
        for seed in seeds:
            _, fit, info = run_one(
                TLEMultiAction, problem_name, seed, llm=llm,
                trigger="triple", scheduler="fixed", budget=budget,
            )
            tlema_bests.append(best_fitness(fit))
        avg = np.mean(tlema_bests)
        std = np.std(tlema_bests)
        print(f"TLE-MA budget={budget:3d}: avg={avg:.4f} +/- {std:.4f}  "
              f"(vs DE: {(avg - np.mean(de_bests))/np.mean(de_bests)*100:+.2f}%)")


if __name__ == "__main__":
    main()