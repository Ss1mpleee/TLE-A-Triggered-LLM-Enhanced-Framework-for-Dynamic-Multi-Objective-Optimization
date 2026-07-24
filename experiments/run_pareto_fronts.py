"""Run DE/DNSGA-II-A/TLE on DF1+DF5+DF7 with 3 seeds and save final populations.

Used to plot Pareto fronts in SM S5 (fig_pareto_dispatch.png).
Main paper already shows DF2 (catastrophic failure), SM shows DF1+DF5+DF7.
"""
import sys
sys.path.insert(0, r'D:\新论文\实验')

import json
import time
import numpy as np
from pathlib import Path
from core import LLMClient, TLE, DEBaseline, DNSGAIIA, DEFAULT_MODEL
from core.moo_utils import compute_igd, fast_non_dominated_sort
from benchmarks import DMOProblem, get_reference_pf

OUT = Path(r'D:\新论文\实验\results\raw\exp_pareto_fronts.json')

ALGOS = ['DE', 'DNSGA-II-A', 'TLE']
PROBLEMS = ['DF1', 'DF5', 'DF7']
SEEDS = [0, 1, 2]
POP_SIZE = 50
MAX_GEN = 200


def run_de(problem, seed):
    np.random.seed(seed)
    de = DEBaseline(d=10, bounds=(problem.lower, problem.upper), n_obj=problem.M,
                    pop_size=POP_SIZE, max_gen=MAX_GEN, F=0.5, CR=0.9, seed=seed)
    pop, fit, _ = de.optimize(problem.evaluate, problem=problem)
    fronts = fast_non_dominated_sort(fit)
    nd = fit[fronts[0]] if fronts else fit
    return nd


def run_dnsga(problem, seed):
    np.random.seed(seed)
    algo = DNSGAIIA(d=10, bounds=(problem.lower, problem.upper), n_obj=problem.M,
                    pop_size=POP_SIZE, max_gen=MAX_GEN, seed=seed)
    pop, fit, _ = algo.optimize(problem.evaluate, problem=problem)
    fronts = fast_non_dominated_sort(fit)
    nd = fit[fronts[0]] if fronts else fit
    return nd


def run_tle(problem, seed):
    np.random.seed(seed)
    llm = LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True)
    algo = TLE(
        d=10, bounds=(problem.lower, problem.upper), n_obj=problem.M,
        pop_size=POP_SIZE, max_gen=MAX_GEN, llm=llm,
        trigger='triple', scheduler='heuristic', seed=seed,
    )
    pop, fit, info = algo.optimize(problem.evaluate, problem=problem)
    fronts = fast_non_dominated_sort(fit)
    nd = fit[fronts[0]] if fronts else fit
    return nd


RUNNERS = {'DE': run_de, 'DNSGA-II-A': run_dnsga, 'TLE': run_tle}

results = []
total = len(ALGOS) * len(PROBLEMS) * len(SEEDS)
done = 0
t0 = time.time()
for algo in ALGOS:
    for prob_name in PROBLEMS:
        for seed in SEEDS:
            t_start = time.time()
            problem = DMOProblem(name=prob_name, d=10, nt=10, taut=10)
            nd = RUNNERS[algo](problem, seed)
            elapsed = time.time() - t_start
            done += 1
            print(f'[{done}/{total}] {algo} {prob_name} seed={seed}: '
                  f'|nd|={len(nd)}, t={elapsed:.1f}s', flush=True)
            results.append({
                'algo': algo,
                'problem': prob_name,
                'seed': seed,
                'n_nd': len(nd),
                'pareto_front': nd.tolist(),
            })

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f'\nSaved {len(results)} Pareto front records to {OUT}')
print(f'Total time: {time.time() - t0:.1f}s')