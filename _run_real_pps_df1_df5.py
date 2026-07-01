"""Run REAL PPS-DMOEA on DF1 + DF5 × 5 seeds (200 gen).

This fills in the missing data identified during gap analysis:
sec_main.json had PPS entries that were identical to DE (data integrity
issue). We re-run PPS from scratch using the implemented PPSDMOEA class
(core/tle.py) and the new run_extended.py PPS mode.
"""
import sys
sys.path.insert(0, r'D:\新论文\实验')
import json
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from core import PPSDMOEA, LLMClient
from benchmarks import DMOProblem, get_reference_pf
from core.moo_utils import compute_igd, fast_non_dominated_sort

OUT = Path(r'D:\新论文\实验\results\raw\sec_pps_real_df1_df5.json')

problems = ['DF1', 'DF5']
seeds = [0, 1, 2, 3, 4]
results = []
t0 = time.time()
idx = 0
total = len(problems) * len(seeds)
print(f'=== REAL PPS-DMOEA: DF1+DF5 × 5 seeds, 200 gen, pop=50 ===')
print(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
for problem in problems:
    for seed in seeds:
        idx += 1
        np.random.seed(seed)
        prob = DMOProblem(name=problem, d=10, nt=10, taut=10)
        ref = get_reference_pf(problem, n=100)
        pps = PPSDMOEA(d=10, bounds=(prob.lower, prob.upper), n_obj=prob.M,
                       pop_size=50, max_gen=200, F=0.5, CR=0.9, seed=seed,
                       predict_ratio=0.5)
        t1 = time.time()
        pop, fit, info = pps.optimize(lambda p: prob.evaluate(p), problem=prob)
        elapsed = time.time() - t1
        fronts = fast_non_dominated_sort(fit)
        nd_fit = fit[fronts[0]] if fronts else fit
        try:
            igd = compute_igd(nd_fit, ref)
        except Exception:
            igd = float('inf')
        # Also compute HV
        from core.moo_utils import compute_hv
        try:
            hv = compute_hv(nd_fit, np.array([1.1, 1.1]))
        except Exception:
            hv = 0.0
        r = {
            'algo': 'PPS-DMOEA',
            'problem': problem,
            'seed': seed,
            'max_gen': 200,
            'pop_size': 50,
            'igd': float(igd),
            'hv': float(hv),
            'elapsed_sec': float(elapsed),
            'invocations': 0,
            'best_fitness_history': info['best_fitness_history'],
        }
        results.append(r)
        print(f'  [{idx}/{total}] PPS-DMOEA {problem:4s} seed={seed} -> IGD={igd:.4f} HV={hv:.4f} ({elapsed:.2f}s)')
        with open(OUT, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
print(f'\nTotal: {time.time()-t0:.2f}s')
print(f'Saved to: {OUT}')

# Summary
from collections import defaultdict
by_p = defaultdict(list)
for r in results:
    by_p[r['problem']].append(r['igd'])
for p in probs:
    vals = by_p[p]
    print(f'PPS-DMOEA {p}: {np.mean(vals):.4f} ± {np.std(vals):.4f} (n={len(vals)})')
