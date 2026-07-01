"""
TLE Comprehensive v2 Runner
===========================
Replaces sec_main.json, sec_ablation.json, exp3_uav.json with a complete
5-algo x 5-problem x 5-seed dataset, on the FIXED DMO setup where
problem.step() is now called each generation (change_steps actually fills).

Algos:
  1. DE                  (pure DE, no LLM)
  2. DE-LM-static-trigger (triple-signal trigger + heuristic budget)
  3. PPS-DMOEA           (Zhou 2014 population prediction)
  4. DNSGA-II-A          (Deb 2007 NSGA-II + random immigrants)
  5. TLE                 (triple-signal + UCB bandit + dual-channel)

DMO problems (CEC2018): DF1, DF2, DF3, DF5, DF7  (2-objective)
UAV scenario: 5 algos x 5 seeds x {n_uavs=4, 8} = 50 runs
Ablation: V0-V3 x DF1+DF5 x 5 seeds = 40 runs

Outputs (overwrites old files):
  - sec_main_v2.json    (5 algos x 5 probs x 5 seeds = 125 runs)
  - sec_ablation_v2.json (4 variants x 2 probs x 5 seeds = 40 runs)
  - exp3_uav_v2.json     (5 algos x 5 seeds x 2 n_uavs = 50 runs)
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
    LLMClient, TLE, DEBaseline, PPSDMOEA, DNSGAIIA,
    RandomLMEABaseline, DEFAULT_MODEL
)
from benchmarks import DMOProblem, get_reference_pf
from core.moo_utils import compute_igd, compute_hv, fast_non_dominated_sort

RAW = Path(r'D:\新论文\实验\results\raw')
RAW.mkdir(parents=True, exist_ok=True)


# ============ Main DMO experiment ============
def make_algo(algo_name, d, lower, upper, n_obj, pop_size, max_gen, llm, seed):
    """Factory for the 5 algorithms. Each alg gets its own DMOProblem (per call)."""
    if algo_name == "DE":
        return DEBaseline(d=d, bounds=(lower, upper), n_obj=n_obj,
                          pop_size=pop_size, max_gen=max_gen,
                          F=0.5, CR=0.9, strategy="rand", seed=seed)
    elif algo_name == "DE-LM-static-trigger":
        from core.bandit import HeuristicDecayScheduler
        algo = TLE(d=d, bounds=(lower, upper), n_obj=n_obj,
                   pop_size=pop_size, max_gen=max_gen, llm=llm,
                   trigger="triple", scheduler="heuristic",
                   budget=20, seed=seed)
        return algo
    elif algo_name == "PPS-DMOEA":
        return PPSDMOEA(d=d, bounds=(lower, upper), n_obj=n_obj,
                        pop_size=pop_size, max_gen=max_gen,
                        F=0.5, CR=0.9, seed=seed, predict_ratio=0.5)
    elif algo_name == "DNSGA-II-A":
        return DNSGAIIA(d=d, bounds=(lower, upper), n_obj=n_obj,
                        pop_size=pop_size, max_gen=max_gen,
                        eta_c=20, eta_m=20, immigrant_frac=0.2, seed=seed)
    elif algo_name == "TLE":
        return TLE(d=d, bounds=(lower, upper), n_obj=n_obj,
                   pop_size=pop_size, max_gen=max_gen, llm=llm,
                   trigger="triple", scheduler="bandit", seed=seed)
    else:
        raise ValueError(algo_name)


def run_main(out="sec_main_v2.json",
             algos=("DE", "DE-LM-static-trigger", "PPS-DMOEA", "DNSGA-II-A", "TLE"),
             problems=("DF1", "DF2", "DF3", "DF5", "DF7"),
             seeds=(0, 1, 2, 3, 4),
             pop_size=50, max_gen=200, d=10):
    """Run main DMO comparison."""
    print(f"=== Main DMO: {len(algos)} algos × {len(problems)} probs × {len(seeds)} seeds "
          f"= {len(algos)*len(problems)*len(seeds)} runs ===")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    results = []
    t_start = time.time()
    idx = 0
    total = len(algos) * len(problems) * len(seeds)
    for problem_name in problems:
        for algo_name in algos:
            for seed in seeds:
                idx += 1
                np.random.seed(seed)
                # Fresh problem per run (independent seeds)
                problem = DMOProblem(name=problem_name, d=d, nt=10, taut=10)
                ref_pf = get_reference_pf(problem_name, n=100)

                # Shared LLM cache (helps TLE and DE-LM-static-trigger)
                use_llm = algo_name in ("TLE", "DE-LM-static-trigger")
                llm = (LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True)
                       if use_llm else None)

                algo = make_algo(algo_name, d, problem.lower, problem.upper,
                                 problem.M, pop_size, max_gen, llm, seed)

                t0 = time.time()
                pop, fit, info = algo.optimize(
                    lambda p: problem.evaluate(p), problem=problem
                )
                elapsed = time.time() - t0

                fronts = fast_non_dominated_sort(fit)
                nd_fit = fit[fronts[0]] if fronts else fit
                try:
                    igd = compute_igd(nd_fit, ref_pf)
                except Exception:
                    igd = float("inf")
                ref_point = np.array([1.1] * problem.M)
                try:
                    hv = compute_hv(nd_fit, ref_point)
                except Exception:
                    hv = 0.0

                r = {
                    "algo": algo_name,
                    "problem": problem_name,
                    "seed": seed,
                    "max_gen": max_gen,
                    "pop_size": pop_size,
                    "igd": float(igd),
                    "hv": float(hv),
                    "elapsed_sec": float(elapsed),
                    "invocations": info.get("invocations", 0),
                }
                results.append(r)
                inv_str = f"inv={r['invocations']:3d}" if r['invocations'] else "inv=  0"
                print(f"  [{idx:3d}/{total}] {algo_name:22s} {problem_name:4s} "
                      f"seed={seed}  IGD={igd:.4f}  HV={hv:.4f}  {inv_str}  ({elapsed:.1f}s)")
                with open(RAW / out, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nMain total: {time.time() - t_start:.1f}s")
    return results


# ============ Ablation ============
def run_ablation(out="sec_ablation_v2.json",
                 seeds=(0, 1, 2, 3, 4), pop_size=50, max_gen=200, d=10):
    print(f"\n=== Ablation: V0-V3 × DF1+DF5 × {len(seeds)} seeds = 40 runs ===")
    variants = [
        ("V0_TLE_full",         dict(trigger="triple",  scheduler="bandit",    llm=True)),
        ("V1_single_signal",    dict(trigger="single",  scheduler="bandit",    llm=True)),
        ("V2_heuristic_budget", dict(trigger="triple",  scheduler="heuristic", llm=True)),
        ("V3_no_llm",           dict(trigger="never",   scheduler="bandit",    llm=False)),
    ]
    problems = ["DF1", "DF5"]
    results = []
    t_start = time.time()
    idx = 0
    total = len(variants) * len(problems) * len(seeds)
    for variant_name, kw in variants:
        for problem in problems:
            for seed in seeds:
                idx += 1
                np.random.seed(seed)
                problem_obj = DMOProblem(name=problem, d=d, nt=10, taut=10)
                ref_pf = get_reference_pf(problem, n=100)
                llm = (LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True)
                       if kw["llm"] else None)
                algo = TLE(d=d, bounds=(problem_obj.lower, problem_obj.upper),
                           n_obj=problem_obj.M, pop_size=pop_size, max_gen=max_gen,
                           llm=llm, trigger=kw["trigger"], scheduler=kw["scheduler"],
                           seed=seed)
                t0 = time.time()
                pop, fit, info = algo.optimize(
                    lambda p: problem_obj.evaluate(p), problem=problem_obj
                )
                elapsed = time.time() - t0
                fronts = fast_non_dominated_sort(fit)
                nd_fit = fit[fronts[0]] if fronts else fit
                try:
                    igd = compute_igd(nd_fit, ref_pf)
                except Exception:
                    igd = float("inf")
                r = {
                    "variant": variant_name,
                    "problem": problem,
                    "seed": seed,
                    "igd": float(igd),
                    "elapsed_sec": float(elapsed),
                    "invocations": info.get("invocations", 0),
                }
                results.append(r)
                inv_str = f"inv={r['invocations']:3d}" if r['invocations'] else "inv=  0"
                print(f"  [{idx:2d}/{total}] {variant_name:25s} {problem:4s} seed={seed} "
                      f"IGD={igd:.4f}  {inv_str}  ({elapsed:.1f}s)")
                with open(RAW / out, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nAblation total: {time.time() - t_start:.1f}s")
    return results


# ============ UAV ============
def run_uav(out="exp3_uav_v2.json",
            algos=("DE", "DE-LM-static-trigger", "PPS-DMOEA", "DNSGA-II-A", "TLE"),
            seeds=(0, 1, 2, 3, 4), n_uavs_list=(4, 8),
            pop_size=30, max_gen=60):
    print(f"\n=== UAV: {len(algos)} algos × {len(seeds)} seeds × {len(n_uavs_list)} n_uavs "
          f"= {len(algos)*len(seeds)*len(n_uavs_list)} runs ===")
    from benchmarks import (ScenarioConfig, generate_scenario,
                            evaluate_uav_solution)
    _current_scenario = [None]  # avoid global
    results = []
    t_start = time.time()
    idx = 0
    total = len(algos) * len(seeds) * len(n_uavs_list)
    for n_uavs in n_uavs_list:
        for seed in seeds:
            np.random.seed(seed)
            cfg = ScenarioConfig(n_uavs=n_uavs, simulation_time=300.0,
                                 task_arrival_rate=0.3, seed=seed)
            _current_scenario[0] = generate_scenario(cfg)
            n_tasks = len(_current_scenario[0]["tasks"])
            D = n_uavs * n_tasks
            print(f"\n  [n_uavs={n_uavs}, seed={seed}] tasks={n_tasks} D={D}")

            for algo_name in algos:
                idx += 1
                np.random.seed(seed)
                use_llm = algo_name in ("TLE", "DE-LM-static-trigger")
                llm = (LLMClient(model=DEFAULT_MODEL, max_tokens=400, use_cache=True)
                       if use_llm else None)

                if algo_name == "DE":
                    algo = DEBaseline(d=D, bounds=(np.zeros(D), np.ones(D)),
                                      n_obj=3, pop_size=pop_size, max_gen=max_gen,
                                      F=0.5, CR=0.9, strategy="rand", seed=seed)
                elif algo_name == "DE-LM-static-trigger":
                    algo = TLE(d=D, bounds=(np.zeros(D), np.ones(D)), n_obj=3,
                               pop_size=pop_size, max_gen=max_gen, llm=llm,
                               trigger="triple", scheduler="heuristic",
                               budget=max_gen // 4, seed=seed)
                elif algo_name == "PPS-DMOEA":
                    algo = PPSDMOEA(d=D, bounds=(np.zeros(D), np.ones(D)),
                                    n_obj=3, pop_size=pop_size, max_gen=max_gen,
                                    F=0.5, CR=0.9, seed=seed, predict_ratio=0.5)
                elif algo_name == "DNSGA-II-A":
                    algo = DNSGAIIA(d=D, bounds=(np.zeros(D), np.ones(D)),
                                    n_obj=3, pop_size=pop_size, max_gen=max_gen,
                                    eta_c=20, eta_m=20, immigrant_frac=0.2,
                                    seed=seed)
                else:  # TLE
                    algo = TLE(d=D, bounds=(np.zeros(D), np.ones(D)), n_obj=3,
                               pop_size=pop_size, max_gen=max_gen, llm=llm,
                               trigger="triple", scheduler="bandit", seed=seed)

                def evaluate(pop):
                    NP = pop.shape[0]
                    fits = np.zeros((NP, 3))
                    for i in range(NP):
                        fits[i] = evaluate_uav_solution(pop[i], _current_scenario[0])
                    return fits

                t0 = time.time()
                pop, fit, info = algo.optimize(evaluate)
                elapsed = time.time() - t0

                fronts = fast_non_dominated_sort(fit)
                nd_fit = fit[fronts[0]] if fronts else fit
                f1_value = -np.min(nd_fit[:, 0]) if len(nd_fit) else 0
                f2_time = -np.min(nd_fit[:, 1]) if len(nd_fit) else 600
                f3_batt = -np.max(nd_fit[:, 2]) if len(nd_fit) else 0
                try:
                    hv = compute_hv(nd_fit - np.array([0, 0, 0]),
                                    np.array([f1_value + 1, f2_time + 1, f3_batt + 1]))
                except Exception:
                    hv = 0.0
                r = {
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
                results.append(r)
                inv_str = f"inv={r['invocations']:3d}" if r['invocations'] else "inv=  0"
                print(f"    [{idx:2d}/{total}] {algo_name:22s} value={f1_value:.1f} "
                      f"time={f2_time:.1f}s batt={f3_batt:.1f}% {inv_str} ({elapsed:.1f}s)")
                with open(RAW / out, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nUAV total: {time.time() - t_start:.1f}s")
    return results


# ============ Main ============
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["main", "ablation", "uav", "all"],
                        default="all")
    args = parser.parse_args()

    if args.mode in ("main", "all"):
        run_main()
    if args.mode in ("ablation", "all"):
        run_ablation()
    if args.mode in ("uav", "all"):
        run_uav()

    print("\n=== ALL DONE ===")


if __name__ == "__main__":
    main()
