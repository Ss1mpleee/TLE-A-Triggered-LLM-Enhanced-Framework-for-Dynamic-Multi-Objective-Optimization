"""Re-run DF3 for all algos × 5 seeds, with fixed code (clamp + IGD/HV safety)."""
import sys
sys.path.insert(0, r'D:\新论文\实验')
import json
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from core import LLMClient, TLE, DEBaseline, PPSDMOEA, DNSGAIIA, DEFAULT_MODEL
from benchmarks import DMOProblem, get_reference_pf
from core.moo_utils import compute_igd, compute_hv, fast_non_dominated_sort

OUT = Path(r'D:\新论文\实验\results\raw\df3_fix.json')
MAIN_FILE = Path(r'D:\新论文\实验\results\raw\sec_main_v2.json')

algos = ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A', 'TLE']
seeds = [0, 1, 2, 3, 4]
results = []
t0 = time.time()
print(f'=== DF3 fix re-run (5 algos × 5 seeds = 25 runs) ===\n')
for algo_name in algos:
    for seed in seeds:
        np.random.seed(seed)
        prob = DMOProblem('DF3', d=10, nt=10, taut=10)
        ref = get_reference_pf('DF3', n=100)
        use_llm = algo_name in ('TLE', 'DE-LM-static-trigger')
        llm = (LLMClient(model=DEFAULT_MODEL, max_tokens=500, use_cache=True)
               if use_llm else None)
        if algo_name == 'DE':
            algo = DEBaseline(d=10, bounds=(prob.lower, prob.upper), n_obj=prob.M,
                              pop_size=50, max_gen=200, F=0.5, CR=0.9,
                              strategy='rand', seed=seed)
        elif algo_name == 'DE-LM-static-trigger':
            algo = TLE(d=10, bounds=(prob.lower, prob.upper), n_obj=prob.M,
                       pop_size=50, max_gen=200, llm=llm, trigger='triple',
                       scheduler='heuristic', budget=20, seed=seed)
        elif algo_name == 'PPS-DMOEA':
            algo = PPSDMOEA(d=10, bounds=(prob.lower, prob.upper), n_obj=prob.M,
                            pop_size=50, max_gen=200, F=0.5, CR=0.9,
                            seed=seed, predict_ratio=0.5)
        elif algo_name == 'DNSGA-II-A':
            algo = DNSGAIIA(d=10, bounds=(prob.lower, prob.upper), n_obj=prob.M,
                            pop_size=50, max_gen=200, eta_c=20, eta_m=20,
                            immigrant_frac=0.2, seed=seed)
        else:  # TLE
            algo = TLE(d=10, bounds=(prob.lower, prob.upper), n_obj=prob.M,
                       pop_size=50, max_gen=200, llm=llm, trigger='triple',
                       scheduler='bandit', seed=seed)
        ts = time.time()
        pop, fit, info = algo.optimize(lambda p: prob.evaluate(p), problem=prob)
        elapsed = time.time() - ts
        fronts = fast_non_dominated_sort(fit)
        nd_fit = fit[fronts[0]] if fronts else fit
        try:
            igd = compute_igd(nd_fit, ref)
        except Exception:
            igd = float('inf')
        try:
            hv = compute_hv(nd_fit, np.array([1.1, 1.1]))
        except Exception:
            hv = 0.0
        r = {
            'algo': algo_name,
            'problem': 'DF3',
            'seed': seed,
            'max_gen': 200,
            'pop_size': 50,
            'igd': float(igd),
            'hv': float(hv),
            'elapsed_sec': float(elapsed),
            'invocations': info.get('invocations', 0),
        }
        results.append(r)
        print(f'  {algo_name:22s} DF3 seed={seed} IGD={igd:.4f} HV={hv:.4f} '
              f'inv={r["invocations"]:3d} ({elapsed:.1f}s)')
        with open(OUT, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

# Merge into sec_main_v2.json
print(f'\nMerging DF3 results into {MAIN_FILE}...')
main_data = json.load(open(MAIN_FILE, encoding='utf-8'))
# Remove any DF3 entries
main_data = [r for r in main_data if r.get('problem') != 'DF3']
# Add new DF3 entries
main_data.extend(results)
with open(MAIN_FILE, 'w', encoding='utf-8') as f:
    json.dump(main_data, f, ensure_ascii=False, indent=2)
print(f'  Main file now has {len(main_data)} entries (was {len(main_data)-len(results)})')
print(f'\nTotal: {time.time()-t0:.1f}s')

# Summary
from collections import defaultdict
by_a = defaultdict(list)
for r in results:
    by_a[r['algo']].append(r['igd'])
print('\nDF3 IGD summary (5 seeds each):')
for a in algos:
    vals = by_a[a]
    print(f'  {a:22s}: {np.mean(vals):.4f} ± {np.std(vals):.4f}')
