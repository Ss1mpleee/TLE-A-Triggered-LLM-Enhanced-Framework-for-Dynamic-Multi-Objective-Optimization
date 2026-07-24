"""
Quick timing test for 16/32-UAV scenarios.
"""
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\新论文\实验")
sys.path.insert(0, str(ROOT))

import numpy as np
from core.tle import DEBaseline, TLE, DNSGAIIA
from core.llm_interface import LLMClient
from benchmarks.uav_scenario import (
    ScenarioConfig, generate_scenario, evaluate_uav_solution,
)


def run_quick(algo_name, n_uavs, seed, pop_size, max_gen, llm=None):
    np.random.seed(seed)
    cfg = ScenarioConfig(
        n_uavs=n_uavs,
        simulation_time=300.0,
        task_arrival_rate=0.3,
        seed=seed,
    )
    scenario = generate_scenario(cfg)
    scenario["n_uavs"] = n_uavs
    n_tasks = len(scenario["tasks"])
    D = n_uavs * n_tasks
    bounds = (np.zeros(D), np.ones(D))

    if algo_name == "DE":
        algo = DEBaseline(d=D, bounds=bounds, n_obj=3, pop_size=pop_size, max_gen=max_gen, seed=seed)
    elif algo_name == "TLE":
        algo = TLE(d=D, bounds=bounds, n_obj=3, pop_size=pop_size, max_gen=max_gen, llm=llm,
                   trigger="triple", scheduler="heuristic", seed=seed)
    elif algo_name == "DNSGA-II-A":
        algo = DNSGAIIA(d=D, bounds=bounds, n_obj=3, pop_size=pop_size, max_gen=max_gen, seed=seed)
    else:
        raise ValueError(algo_name)

    def evaluate(pop):
        NP = pop.shape[0]
        fits = np.zeros((NP, 3))
        for i in range(NP):
            fits[i] = evaluate_uav_solution(pop[i], scenario)
        return fits

    t0 = time.time()
    pop, fit, info = algo.optimize(evaluate)
    elapsed = time.time() - t0
    return {
        "n_uavs": n_uavs,
        "n_tasks": n_tasks,
        "D": D,
        "algo": algo_name,
        "elapsed": elapsed,
        "pop_size": pop_size,
        "max_gen": max_gen,
        "f1": -float(np.min(fit[:, 0])),
        "invocations": info.get("invocations", 0),
    }


def main():
    print("=== UAV scalability quick timing test ===\n")
    llm = LLMClient(model="qwen2.5:7b", use_cache=True)

    for n_uavs in [16, 32]:
        # pop_size scales with n_uavs
        pop_size = 60 if n_uavs == 16 else 100
        max_gen = 40

        print(f"\n--- n_uavs={n_uavs}, pop_size={pop_size}, max_gen={max_gen} ---")
        for algo in ["DE", "DNSGA-II-A", "TLE"]:
            t0 = time.time()
            res = run_quick(algo, n_uavs, seed=0, pop_size=pop_size, max_gen=max_gen, llm=llm)
            print(f"  {algo}: n_tasks={res['n_tasks']}, D={res['D']}, "
                  f"f1={res['f1']:.1f}, time={res['elapsed']:.1f}s, "
                  f"inv={res['invocations']}")


if __name__ == "__main__":
    main()