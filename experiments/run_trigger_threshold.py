"""Trigger entropy_threshold sensitivity sweep.

The triple-signal trigger fires when entropy drop > entropy_threshold.
Sweep entropy_threshold in [0.001, 0.01, 0.05, 0.1, 0.5] on DF1+DF5
with 3 seeds, fixed scheduler (no budget cap).

Result: how does trigger sensitivity affect IGD vs invocations?
Output: results/raw/exp_trigger_threshold.json
"""
import sys
sys.path.insert(0, r'D:\新论文\实验')

import json
import time
import numpy as np
from pathlib import Path
from core import LLMClient, TLE, DEFAULT_MODEL
from core.bandit import FixedBudgetScheduler
from core.moo_utils import compute_igd, fast_non_dominated_sort
from benchmarks import DMOProblem, get_reference_pf

OUT = Path(r'D:\新论文\实验\results\raw\exp_trigger_threshold.json')

PROBLEMS = ['DF1', 'DF5']
SEEDS = [0, 1, 2]
ENTROPY_THRESHOLDS = [0.001, 0.01, 0.05, 0.1, 0.5]
POP_SIZE = 50
MAX_GEN = 200


def run_tle_with_threshold(problem, seed, entropy_t):
    np.random.seed(seed)
    llm = LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True)
    algo = TLE(
        d=10, bounds=(problem.lower, problem.upper), n_obj=problem.M,
        pop_size=POP_SIZE, max_gen=MAX_GEN, llm=llm,
        trigger='triple', scheduler='bandit', seed=seed,
    )
    # Override trigger's entropy_threshold
    algo.trigger.entropy_threshold = entropy_t
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
total = len(PROBLEMS) * len(SEEDS) * len(ENTROPY_THRESHOLDS)
done = 0
t0 = time.time()
for prob_name in PROBLEMS:
    for ent_t in ENTROPY_THRESHOLDS:
        for seed in SEEDS:
            t_start = time.time()
            problem = DMOProblem(name=prob_name, d=10, nt=10, taut=10)
            res = run_tle_with_threshold(problem, seed, ent_t)
            elapsed = time.time() - t_start
            done += 1
            print(f'[{done}/{total}] {prob_name} tau_e={ent_t} seed={seed}: '
                  f'IGD={res["igd"]:.4f} inv={res["invocations"]} t={elapsed:.1f}s',
                  flush=True)
            results.append({
                'problem': prob_name,
                'entropy_threshold': ent_t,
                'seed': seed,
                **res,
            })

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f'\nSaved {len(results)} trigger threshold records to {OUT}')
print(f'Total time: {time.time() - t0:.1f}s')