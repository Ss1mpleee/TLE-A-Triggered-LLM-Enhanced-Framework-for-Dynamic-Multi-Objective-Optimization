"""
Quick test for TLEMultiAction (A3 framework).

Runs 5 seeds x DF5 and reports:
  - LLM action distribution (does LLM use all 4 actions?)
  - Best fitness vs DE baseline
  - Total LLM calls / latency

Gate: LLM should pick at least 2 distinct actions, not always "param".
"""
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\新论文\实验")
sys.path.insert(0, str(ROOT))

import numpy as np
from core.tle import TLEMultiAction, DEBaseline
from core.llm_interface import LLMClient
from benchmarks.cec2018 import DMOProblem


def run_one(algo_cls, problem_name, seed, llm=None, max_gen=80, **algo_kwargs):
    """Run one algorithm on one problem."""
    problem = DMOProblem(name=problem_name, d=10, nt=10, taut=10)
    # DEBaseline doesn't accept llm kwarg
    if algo_cls is DEBaseline:
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


def main():
    model = "qwen2.5:7b"

    print(f"=== TLE-MA quick test (model={model}) ===")
    print("Problem: DF5, 5 seeds, 80 gens")
    print()

    llm = LLMClient(model=model, temperature=0.0)

    de_bests = []
    tlema_bests = []
    tlema_actions = []

    for seed in [0, 1, 2, 3, 4]:
        print(f"--- seed {seed} ---")
        t0 = time.time()
        _, fit_de, info_de = run_one(DEBaseline, "DF5", seed)
        best_de = float(np.min(np.sum(fit_de, axis=1)))
        de_bests.append(best_de)
        print(f"  DE: best={best_de:.3f}, time={time.time()-t0:.1f}s")

        t0 = time.time()
        _, fit_tlema, info_tlema = run_one(
            TLEMultiAction, "DF5", seed, llm=llm,
            trigger="triple", scheduler="heuristic",
        )
        best_tlema = float(np.min(np.sum(fit_tlema, axis=1)))
        tlema_bests.append(best_tlema)
        tlema_actions.append(info_tlema["action_distribution"])
        inv = info_tlema["invocations"]
        llm_calls = (info_tlema["llm_stats"]["total_calls"]
                     if info_tlema.get("llm_stats") else 0)
        print(f"  TLE-MA: best={best_tlema:.3f}, time={time.time()-t0:.1f}s, "
              f"inv={inv}, llm_calls={llm_calls}")
        print(f"    actions: {info_tlema['action_distribution']}")

    print()
    print("=== Summary ===")
    print(f"DE best avg:     {np.mean(de_bests):.3f} +/- {np.std(de_bests):.3f}")
    print(f"TLE-MA best avg: {np.mean(tlema_bests):.3f} +/- {np.std(tlema_bests):.3f}")
    diff_pct = (np.mean(tlema_bests) - np.mean(de_bests)) / np.mean(de_bests) * 100
    print(f"TLE-MA vs DE: {diff_pct:+.2f}% (lower is better for minimization)")
    print()
    from collections import Counter
    merged = Counter()
    for d in tlema_actions:
        merged.update(d)
    total = sum(merged.values())
    print(f"TLE-MA action distribution across 5 seeds (total={total} actions):")
    for k in ["param", "archive_reset", "restart_top", "diversity_injection"]:
        c = merged.get(k, 0)
        pct = 100 * c / max(total, 1)
        print(f"  {k}: {c} ({pct:.1f}%)")
    if total > 0:
        n_actions_used = sum(1 for k in ["param", "archive_reset", "restart_top", "diversity_injection"] if merged.get(k, 0) > 0)
        print(f"\nGate check: LLM used {n_actions_used}/4 distinct actions")
        if n_actions_used >= 2:
            print("  PASS (>= 2 actions used; multi-action is working)")
        else:
            print("  FAIL (LLM only picked 1 action; prompt may need tuning)")


if __name__ == "__main__":
    main()