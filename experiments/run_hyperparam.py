"""Hyperparameter sensitivity: TLE on DF5 with different (F, CR, lambda).

This runs TLE with 3 F values × 3 CR values × 2 lambda values × 3 seeds
= 54 runs on DF5 only.  This is the cheapest hyperparameter sweep that
can demonstrate robustness.
"""
import sys
sys.path.insert(0, r'D:\新论文\实验')

import json
import numpy as np
from pathlib import Path
from collections import defaultdict
from core import LLMClient, TLE, DEFAULT_MODEL
from core.moo_utils import compute_igd, fast_non_dominated_sort
from benchmarks import DMOProblem, get_reference_pf

PROB = 'DF5'
SEEDS = [0, 1, 2]
F_VALUES = [0.3, 0.5, 0.7]
CR_VALUES = [0.7, 0.9, 0.95]
LAMBDA_VALUES = [0.05, 0.20]  # default 0.05, high-cost
POP_SIZE = 50
MAX_GEN = 200
# Override scheduler to heuristic to test the sensitivity in heuristic regime
# (F, CR are DE-level, lambda is bandit-level; for heuristic we only vary F, CR)

results = []
for F in F_VALUES:
    for CR in CR_VALUES:
        for lam in LAMBDA_VALUES:
            for seed in SEEDS:
                np.random.seed(seed)
                problem = DMOProblem(name=PROB, d=10, nt=10, taut=10)
                ref_pf = get_reference_pf(PROB, n=100)
                bounds = (problem.lower, problem.upper)

                def evaluate(pop):
                    return problem.evaluate(pop)

                llm = LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True)
                algo = TLE(
                    d=10, bounds=bounds, n_obj=problem.M,
                    pop_size=POP_SIZE, max_gen=MAX_GEN, llm=llm,
                    trigger='triple', scheduler='bandit', seed=seed,
                )
                # Override hyperparameters
                algo.F = F
                algo.CR = CR
                if hasattr(algo.scheduler, 'cost_per_call'):
                    algo.scheduler.cost_per_call = lam
                pop, fit, info = algo.optimize(evaluate, problem=problem)
                # Compute IGD
                fronts = fast_non_dominated_sort(fit)
                nd = fit[fronts[0]] if fronts else fit
                try:
                    igd = float(compute_igd(nd, ref_pf))
                except Exception:
                    igd = float('inf')
                results.append({
                    'F': F, 'CR': CR, 'lambda': lam, 'seed': seed,
                    'igd': igd,
                    'invocations': info.get('invocations', 0),
                })
                print(f'F={F} CR={CR} λ={lam} seed={seed}: IGD={igd:.4f} '
                      f'inv={info.get("invocations", 0)}')

out = Path(r'D:\新论文\实验\results\raw\exp5_hyperparam.json')
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f'\nSaved {len(results)} hyperparameter runs to {out}')
