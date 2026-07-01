"""
Extended Experiments Runner
===========================
Fills in the missing data identified in the SCI gap analysis:
  1. Ablation: V0-V3 × DF1+DF5 × seeds 3, 4  (8 new runs, total becomes 5 seeds)
  2. UAV: 4 algos × 5 seeds × {n_uavs=4, n_uavs=8}  (40 runs total = 20 new at 5 seeds)
  3. PPS-DMOEA: DF2/DF3/DF7 × 5 seeds  (15 new runs)

Writes to:
  - sec_ablation_v2.json   (extending sec_ablation.json with seeds 3, 4)
  - exp3_uav_v2.json        (5 seeds × 2 n_uavs configs)
  - sec_pps_extended.json   (PPS on DF2/DF3/DF7)

Existing data (sec_main.json, sec_ablation.json, exp3_uav.json) is left
untouched; this script only ADDS new runs.
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
    LLMClient, TLE, DEBaseline, PPSDMOEA, DEFAULT_MODEL
)
from benchmarks import DMOProblem, get_reference_pf
from core.moo_utils import compute_igd, compute_hv, fast_non_dominated_sort


RAW_DIR = Path("D:/新论文/实验/results/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


# ==================== Helpers ====================
def evaluate_cec(problem, pop):
    return problem.evaluate(pop)


def run_cec_single(algo_name, problem_name, seed,
                   pop_size=50, max_gen=200, d=10, use_llm=True):
    """Run a single (algo, problem, seed) on CEC2018 DMO."""
    np.random.seed(seed)
    problem = DMOProblem(name=problem_name, d=d, nt=10, taut=10)
    ref_pf = get_reference_pf(problem_name, n=100)

    llm = None
    if use_llm and algo_name in ("TLE",):
        llm = LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True)

    if algo_name == "DE":
        algo = DEBaseline(d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
                          pop_size=pop_size, max_gen=max_gen,
                          F=0.5, CR=0.9, strategy="rand", seed=seed)
    elif algo_name == "PPS-DMOEA":
        algo = PPSDMOEA(d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
                        pop_size=pop_size, max_gen=max_gen,
                        F=0.5, CR=0.9, seed=seed, predict_ratio=0.5)
    else:  # TLE
        algo = TLE(d=d, bounds=(problem.lower, problem.upper), n_obj=problem.M,
                   pop_size=pop_size, max_gen=max_gen, llm=llm,
                   trigger="triple", scheduler="bandit", seed=seed)

    t0 = time.time()
    pop, fit, info = algo.optimize(lambda p: evaluate_cec(problem, p), problem=problem)
    elapsed = time.time() - t0

    # Compute IGD / HV
    fronts = fast_non_dominated_sort(fit)
    nd_fit = fit[fronts[0]] if fronts else fit
    try:
        igd = compute_igd(nd_fit, ref_pf)
    except Exception:
        igd = float("inf")
    ref_point = np.array([1.1, 1.1]) if problem.M == 2 else np.array([1.1]*problem.M)
    try:
        hv = compute_hv(nd_fit, ref_point)
    except Exception:
        hv = 0.0

    return {
        "algo": algo_name,
        "problem": problem_name,
        "seed": seed,
        "max_gen": max_gen,
        "pop_size": pop_size,
        "igd": float(igd),
        "hv": float(hv),
        "elapsed_sec": float(elapsed),
        "invocations": info.get("invocations", 0),
        "best_fitness_history": info.get("best_fitness_history", []),
    }


# ==================== Ablation (4 variants × 2 problems × seeds 3, 4) ====================
def run_ablation_extra(seeds=[3, 4], output="sec_ablation_v2.json"):
    """Run V0-V3 × DF1+DF5 × seeds 3, 4 (extends existing sec_ablation.json)."""
    print("=== Ablation extension (seeds 3, 4) ===")
    variants = [
        ("V0_TLE_full",        dict(trigger="triple",  scheduler="bandit",  llm=True)),
        ("V1_single_signal",   dict(trigger="single",  scheduler="bandit",  llm=True)),
        ("V2_heuristic_budget",dict(trigger="triple",  scheduler="heuristic",llm=True)),
        ("V3_no_llm",          dict(trigger="never",   scheduler="bandit",  llm=False)),
    ]
    problems = ["DF1", "DF5"]
    results = []
    t_start = time.time()
    total = len(variants) * len(problems) * len(seeds)
    idx = 0
    for variant_name, kw in variants:
        for problem in problems:
            for seed in seeds:
                idx += 1
                np.random.seed(seed)
                problem_obj = DMOProblem(name=problem, d=10, nt=10, taut=10)
                ref_pf = get_reference_pf(problem, n=100)
                llm = None
                if kw["llm"]:
                    llm = LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True)
                algo = TLE(d=10, bounds=(problem_obj.lower, problem_obj.upper),
                           n_obj=problem_obj.M, pop_size=50, max_gen=200, llm=llm,
                           trigger=kw["trigger"], scheduler=kw["scheduler"], seed=seed)
                t0 = time.time()
                pop, fit, info = algo.optimize(lambda p: problem_obj.evaluate(p), problem=problem_obj)
                elapsed = time.time() - t0
                fronts = fast_non_dominated_sort(fit)
                nd_fit = fit[fronts[0]] if fronts else fit
                try:
                    igd = compute_igd(nd_fit, ref_pf)
                except Exception:
                    igd = float("inf")
                result = {
                    "variant": variant_name,
                    "problem": problem,
                    "seed": seed,
                    "igd": float(igd),
                    "elapsed_sec": float(elapsed),
                    "invocations": info.get("invocations", 0),
                }
                results.append(result)
                print(f"  [{idx}/{total}] {variant_name:25s} {problem:4s} seed={seed} "
                      f"-> IGD={igd:.4f} ({elapsed:.1f}s)")
                # Save intermediate
                out_path = RAW_DIR / output
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"  Total ablation time: {time.time() - t_start:.1f}s")
    return results


# ==================== UAV (5 seeds × {4 UAV, 8 UAV} × 4 algos) ====================
def run_uav_extended(seeds=[0, 1, 2, 3, 4], n_uavs_list=[4, 8],
                     pop_size=30, max_gen=60, output="exp3_uav_v2.json"):
    """Run UAV experiment: 4 algos × seeds × n_uavs configs."""
    print("\n=== UAV extended experiment ===")
    global _current_scenario
    algos = ["DE", "DE-LM-always", "DE-LM-random", "TLE"]
    results = []
    t_start = time.time()
    total = len(algos) * len(seeds) * len(n_uavs_list)
    idx = 0
    for n_uavs in n_uavs_list:
        for seed in seeds:
            cfg_seed = seed  # scenario seed = run seed
            from benchmarks import ScenarioConfig, generate_scenario, evaluate_uav_solution
            cfg = ScenarioConfig(n_uavs=n_uavs, simulation_time=300.0,
                                 task_arrival_rate=0.3, seed=cfg_seed)
            _current_scenario = generate_scenario(cfg)
            n_tasks = len(_current_scenario["tasks"])
            D = n_uavs * n_tasks
            print(f"\n  [n_uavs={n_uavs}, seed={seed}] tasks={n_tasks} D={D}")

            for algo_name in algos:
                idx += 1
                np.random.seed(seed)
                use_llm = algo_name in ("TLE", "DE-LM-always", "DE-LM-random")
                llm = (LLMClient(model=DEFAULT_MODEL, max_tokens=400, use_cache=True)
                       if use_llm else None)

                if algo_name == "DE":
                    algo = DEBaseline(d=D, bounds=(np.zeros(D), np.ones(D)), n_obj=3,
                                      pop_size=pop_size, max_gen=max_gen,
                                      F=0.5, CR=0.9, strategy="rand", seed=seed)
                elif algo_name == "DE-LM-always":
                    from core.bandit import FixedBudgetScheduler
                    algo = TLE(d=D, bounds=(np.zeros(D), np.ones(D)), n_obj=3,
                               pop_size=pop_size, max_gen=max_gen, llm=llm,
                               trigger="always", scheduler="fixed",
                               budget=max_gen // 4, seed=seed)
                elif algo_name == "DE-LM-random":
                    algo = TLE(d=D, bounds=(np.zeros(D), np.ones(D)), n_obj=3,
                               pop_size=pop_size, max_gen=max_gen, llm=llm,
                               trigger="random", scheduler="fixed",
                               budget=int(max_gen * 0.1), seed=seed)
                else:  # TLE
                    algo = TLE(d=D, bounds=(np.zeros(D), np.ones(D)), n_obj=3,
                               pop_size=pop_size, max_gen=max_gen, llm=llm,
                               trigger="triple", scheduler="bandit", seed=seed)

                def evaluate(pop):
                    NP = pop.shape[0]
                    fits = np.zeros((NP, 3))
                    for i in range(NP):
                        fits[i] = evaluate_uav_solution(pop[i], _current_scenario)
                    return fits

                t0 = time.time()
                pop, fit, info = algo.optimize(evaluate)
                elapsed = time.time() - t0

                fronts = fast_non_dominated_sort(fit)
                nd_fit = fit[fronts[0]] if fronts else fit
                f1_value = -np.min(nd_fit[:, 0]) if len(nd_fit) else 0
                f2_time  = -np.min(nd_fit[:, 1]) if len(nd_fit) else 600
                f3_batt  = -np.max(nd_fit[:, 2]) if len(nd_fit) else 0
                try:
                    hv = compute_hv(nd_fit - np.array([0, 0, 0]),
                                    np.array([f1_value + 1, f2_time + 1, f3_batt + 1]))
                except Exception:
                    hv = 0.0
                result = {
                    "algo": algo_name,
                    "seed": seed,
                    "n_uavs": n_uavs,
                    "n_tasks": n_tasks,
                    "f1_value": float(f1_value),
                    "f2_response_time": float(f2_time),
                    "f3_battery": float(f3_batt),
                    "hv": float(hv),
                    "elapsed_sec": float(elapsed),
                    "invocations": info.get("invocations", 0),
                }
                results.append(result)
                print(f"    [{idx}/{total}] {algo_name:18s} -> value={f1_value:.1f}, "
                      f"time={f2_time:.1f}s, batt={f3_batt:.1f}%, "
                      f"inv={result['invocations']} ({elapsed:.1f}s)")
                out_path = RAW_DIR / output
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n  Total UAV time: {time.time() - t_start:.1f}s")
    return results


# ==================== PPS extended (DF2/DF3/DF7 × 5 seeds) ====================
def run_pps_extended(seeds=[0, 1, 2, 3, 4], output="sec_pps_extended.json"):
    """PPS-DMOEA on DF2/DF3/DF7 × 5 seeds (DF1/DF5 already in sec_main.json)."""
    print("\n=== PPS-DMOEA extended (DF2/DF3/DF7 × 5 seeds) ===")
    problems = ["DF2", "DF3", "DF7"]
    results = []
    t_start = time.time()
    total = len(problems) * len(seeds)
    idx = 0
    for problem in problems:
        for seed in seeds:
            idx += 1
            r = run_cec_single("PPS-DMOEA", problem, seed, use_llm=False)
            r["max_gen"] = 200
            results.append(r)
            print(f"  [{idx}/{total}] PPS-DMOEA {problem:4s} seed={seed} "
                  f"-> IGD={r['igd']:.4f} ({r['elapsed_sec']:.1f}s)")
            out_path = RAW_DIR / output
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"  Total PPS time: {time.time() - t_start:.1f}s")
    return results


# ==================== Main ====================
_global_scenario = None
_current_scenario = None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["ablation", "uav", "pps", "all"],
                        default="all")
    parser.add_argument("--seeds", nargs="+", type=int, default=None,
                        help="Override seeds (default = algorithm-specific)")
    args = parser.parse_args()

    print(f"=== TLE Extended Experiments ===")
    print(f"Mode: {args.mode}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    if args.mode in ("ablation", "all"):
        seeds = args.seeds or [3, 4]
        run_ablation_extra(seeds=seeds)
    if args.mode in ("pps", "all"):
        seeds = args.seeds or [0, 1, 2, 3, 4]
        run_pps_extended(seeds=seeds)
    if args.mode in ("uav", "all"):
        seeds = args.seeds or [0, 1, 2, 3, 4]
        run_uav_extended(seeds=seeds)

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
