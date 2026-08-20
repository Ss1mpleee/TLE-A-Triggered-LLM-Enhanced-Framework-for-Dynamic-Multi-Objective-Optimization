"""Re-run 6 algos on DF2 seed 0 only, capture final non-dominated fronts.

This is the focused experiment that produces fig_pareto_front_df2 in
the main paper (the seed-0 scatter plot of all 6 algorithms' final
non-dominated sets on the DF2 Type-II DMO problem).

Output: D:\新论文\实验\results\raw\exp_df2_seed0_pareto.json
"""
import json
import time
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, r"D:\新论文\实验")

from core import LLMClient, TLE, DEBaseline, DNSGAIIA, PPSDMOEA, DEFAULT_MODEL
from baselines.moea_dd import MOEADD
from core.moo_utils import fast_non_dominated_sort, compute_igd
from benchmarks import DMOProblem, get_reference_pf

OUT = Path(r"D:\新论文\实验\results\raw\exp_df2_seed0_pareto.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

PROBLEM = "DF2"
SEED = 0
NP = 50
MAX_GEN = 200
D = 10


def run_de(problem, seed):
    np.random.seed(seed)
    algo = DEBaseline(
        d=D, bounds=(problem.lower, problem.upper), n_obj=problem.M,
        pop_size=NP, max_gen=MAX_GEN, F=0.5, CR=0.9, strategy="rand", seed=seed,
    )
    pop, fit, info = algo.optimize(problem.evaluate, problem=problem)
    fronts = fast_non_dominated_sort(fit)
    return fit[fronts[0]] if fronts else fit, info.get("invocations", 0)


def run_dnsga(problem, seed):
    np.random.seed(seed)
    algo = DNSGAIIA(
        d=D, bounds=(problem.lower, problem.upper), n_obj=problem.M,
        pop_size=NP, max_gen=MAX_GEN, seed=seed,
    )
    pop, fit, info = algo.optimize(problem.evaluate, problem=problem)
    fronts = fast_non_dominated_sort(fit)
    return fit[fronts[0]] if fronts else fit, info.get("invocations", 0)


def run_pps(problem, seed):
    np.random.seed(seed)
    algo = PPSDMOEA(
        d=D, bounds=(problem.lower, problem.upper), n_obj=problem.M,
        pop_size=NP, max_gen=MAX_GEN, seed=seed,
    )
    pop, fit, info = algo.optimize(problem.evaluate, problem=problem)
    fronts = fast_non_dominated_sort(fit)
    return fit[fronts[0]] if fronts else fit, info.get("invocations", 0)


def run_moeadd(problem, seed):
    np.random.seed(seed)
    algo = MOEADD(
        d=D, bounds=(problem.lower, problem.upper), n_obj=problem.M,
        pop_size=NP, max_gen=MAX_GEN, seed=seed,
    )
    pop, fit, info = algo.optimize(problem.evaluate, problem=problem)
    fronts = fast_non_dominated_sort(fit)
    return fit[fronts[0]] if fronts else fit, info.get("invocations", 0)


def run_de_lm_static(problem, seed, llm):
    np.random.seed(seed)
    # Per run_main_cec2018.py: "DE-LM-static-trigger" maps to TLE with
    # trigger="triple", scheduler="heuristic" (i.e., no bandit).
    algo = TLE(
        d=D, bounds=(problem.lower, problem.upper), n_obj=problem.M,
        pop_size=NP, max_gen=MAX_GEN, llm=llm,
        trigger="triple", scheduler="heuristic", seed=seed,
    )
    pop, fit, info = algo.optimize(problem.evaluate, problem=problem)
    fronts = fast_non_dominated_sort(fit)
    return fit[fronts[0]] if fronts else fit, info.get("invocations", 0)


def run_tle(problem, seed, llm):
    np.random.seed(seed)
    algo = TLE(
        d=D, bounds=(problem.lower, problem.upper), n_obj=problem.M,
        pop_size=NP, max_gen=MAX_GEN, llm=llm,
        trigger="triple", scheduler="bandit", seed=seed,
    )
    pop, fit, info = algo.optimize(problem.evaluate, problem=problem)
    fronts = fast_non_dominated_sort(fit)
    return fit[fronts[0]] if fronts else fit, info.get("invocations", 0)


def main():
    problem = DMOProblem(name=PROBLEM, d=D, nt=10, taut=10)
    ref_pf = get_reference_pf(PROBLEM, n=100)

    llm = LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True)

    runners = [
        ("DE",                       lambda p, s: run_de(p, s)),
        ("DE-LM-static-trigger",     lambda p, s: run_de_lm_static(p, s, llm)),
        ("PPS-DMOEA",                lambda p, s: run_pps(p, s)),
        ("DNSGA-II-A",               lambda p, s: run_dnsga(p, s)),
        ("MOEA/DD",                  lambda p, s: run_moeadd(p, s)),
        ("TLE",                      lambda p, s: run_tle(p, s, llm)),
    ]

    results = []
    for algo_name, runner in runners:
        t0 = time.time()
        nd_fit, inv = runner(problem, SEED)
        elapsed = time.time() - t0
        try:
            igd_val = compute_igd(nd_fit, ref_pf)
            igd_str = f"{igd_val:.4f}"
        except Exception:
            igd_val = float("inf")
            igd_str = "inf"
        print(f"{algo_name:25s} |nd|={len(nd_fit):3d}  inv={inv:3d}  "
              f"IGD={igd_str}  t={elapsed:.1f}s", flush=True)
        results.append({
            "algo": algo_name,
            "problem": PROBLEM,
            "seed": SEED,
            "n_nd": len(nd_fit),
            "invocations": int(inv),
            "igd": float(igd_val) if np.isfinite(igd_val) else None,
            "pareto_front": np.asarray(nd_fit).tolist(),
        })

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(results)} records to {OUT}")


if __name__ == "__main__":
    main()
