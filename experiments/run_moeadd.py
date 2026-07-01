"""Run MOEA/DD baseline on the 5 CEC 2018 DMO problems × 3 seeds.

Output: 实验/results/raw/exp4_moeadd.json
"""
import sys
sys.path.insert(0, r'D:\新论文\实验')

import json
import numpy as np
from pathlib import Path
from collections import defaultdict
from baselines.moea_dd import MOEADD
from benchmarks import DMOProblem, get_reference_pf
from core.moo_utils import compute_igd, compute_hv, fast_non_dominated_sort

PROBS = ['DF1', 'DF2', 'DF3', 'DF5', 'DF7']
SEEDS = [0, 1, 2]
POP_SIZE = 50
MAX_GEN = 200

results = []
for prob in PROBS:
    for seed in SEEDS:
        np.random.seed(seed)
        problem = DMOProblem(name=prob, d=10, nt=10, taut=10)
        ref_pf = get_reference_pf(prob, n=100)
        bounds = (problem.lower, problem.upper)

        def evaluate(pop):
            return problem.evaluate(pop)

        algo = MOEADD(d=10, bounds=bounds, n_obj=problem.M,
                      pop_size=POP_SIZE, max_gen=MAX_GEN, seed=seed)
        pop, fit, info = algo.optimize(evaluate, problem=problem)
        # Compute IGD / HV on final non-dominated set
        fronts = fast_non_dominated_sort(fit)
        nd_fit = fit[fronts[0]] if fronts else fit
        try:
            igd = float(compute_igd(nd_fit, ref_pf))
        except Exception:
            igd = float('inf')
        try:
            ref_point = np.array([1.1, 1.1])
            hv = float(compute_hv(nd_fit, ref_point))
        except Exception:
            hv = 0.0
        results.append({
            'algo': 'MOEA/DD',
            'problem': prob,
            'seed': seed,
            'igd': igd,
            'hv': hv,
        })
        print(f'MOEA/DD | {prob:5s} | seed={seed} | IGD={igd:.4f} | HV={hv:.4f}')

# Save
out = Path(r'D:\新论文\实验\results\raw\exp4_moeadd.json')
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f'\nSaved {len(results)} MOEA/DD runs to {out}')
