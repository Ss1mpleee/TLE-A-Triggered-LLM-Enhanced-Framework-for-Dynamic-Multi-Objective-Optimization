"""Trigger threshold sensitivity sweep.

Sweeps TLE with heuristic scheduler under different LLM budget caps
(1, 2, 3, 4, 5 calls per generation) on DF1 and DF5 with 3 seeds.

Output: results/raw/exp_trigger_sweep.json
"""
import sys
sys.path.insert(0, r'D:\新论文\实验')

import json
import time
import numpy as np
from pathlib import Path
from core import LLMClient, TLE, DEFAULT_MODEL
from core.bandit import HeuristicDecayScheduler
from core.moo_utils import compute_igd, fast_non_dominated_sort
from benchmarks import DMOProblem, get_reference_pf

OUT = Path(r'D:\新论文\实验\results\raw\exp_trigger_sweep.json')

PROBLEMS = ['DF1', 'DF5']
SEEDS = [0, 1, 2]
BUDGET_CAPS = [1, 2, 3, 4, 5]  # max LLM invocations per generation
POP_SIZE = 50
MAX_GEN = 200


def run_tle_with_budget(problem, seed, total_budget):
    np.random.seed(seed)
    llm = LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True)
    algo = TLE(
        d=10, bounds=(problem.lower, problem.upper), n_obj=problem.M,
        pop_size=POP_SIZE, max_gen=MAX_GEN, llm=llm,
        trigger='triple', scheduler='heuristic', seed=seed,
    )
    # Override scheduler total budget
    algo.scheduler.total_budget = total_budget
    algo.scheduler.calls_made = 0
    pop, fit, info = algo.optimize(problem.evaluate, problem=problem)
    fronts = fast_non_dominated_sort(fit)
    nd = fit[fronts[0]] if fronts else fit
    try:
        igd = float(compute_igd(nd, get_reference_pf(problem.name, n=100)))
    except Exception:
        igd = float('inf')
    return {
        'igd': igd,
        'invocations': info.get('invocations', 0),
        'elapsed_sec': info.get('elapsed_sec', 0.0),
    }


results = []
total = len(PROBLEMS) * len(SEEDS) * len(BUDGET_CAPS)
done = 0
t0 = time.time()
for prob_name in PROBLEMS:
    for cap in BUDGET_CAPS:
        for seed in SEEDS:
            t_start = time.time()
            problem = DMOProblem(name=prob_name, d=10, nt=10, taut=10)
            # total_budget = calls_per_gen × total_gen × prob (heuristic)
            # w0=0.5, T=100, t=200 => mean w_t ≈ 0.5*exp(-2) ≈ 0.07
            # so total expected calls ≈ total_budget * 0.07 (clipped)
            # To get ~cap calls per gen over 200 gen, total_budget ~ cap * 200 / 0.07 ≈ cap * 2800
            # But heuristic also has w(t) decay so earlier gens have higher prob
            # Practically, total_budget=cap*50 is enough for ~cap/gen over first 50 gens
            total_budget = cap * 50
            res = run_tle_with_budget(problem, seed, total_budget)
            elapsed = time.time() - t_start
            done += 1
            print(f'[{done}/{total}] {prob_name} cap~{cap}/gen budget={total_budget} seed={seed}: '
                  f'IGD={res["igd"]:.4f} inv={res["invocations"]} t={elapsed:.1f}s',
                  flush=True)
            results.append({
                'problem': prob_name,
                'budget_per_gen_target': cap,
                'total_budget': total_budget,
                'seed': seed,
                **res,
            })

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f'\nSaved {len(results)} trigger sweep records to {OUT}')
print(f'Total time: {time.time() - t0:.1f}s')