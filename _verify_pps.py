"""Verify whether sec_main.json PPS-DMOEA is real or duplicated from DE."""
import json
import numpy as np

sec_main = json.load(open(r'D:\新论文\实验\results\raw\sec_main.json', encoding='utf-8'))

# Build per-(algo, problem, seed) lookup
data = {}
for r in sec_main:
    if 'igd' in r and 'error' not in r:
        key = (r['algo'], r['problem'], r['seed'])
        data[key] = r

print('===== Direct comparison PPS vs DE per (problem, seed) =====')
print(f'{"Prob":5s} {"Seed":4s} {"DE IGD":10s} {"PPS IGD":10s} {"Diff":10s} {"Identical?"}')
for problem in ['DF1', 'DF5']:
    for seed in range(5):
        de = data.get(('DE', problem, seed))
        pps = data.get(('PPS-DMOEA', problem, seed))
        if de and pps:
            identical = abs(de['igd'] - pps['igd']) < 1e-9
            diff = de['igd'] - pps['igd']
            print(f'{problem:5s} {seed:4d} {de["igd"]:.7f}  {pps["igd"]:.7f}  {diff:+.7f}  {"YES (suspicious)" if identical else "no"}')

# Also check best_fitness_history
print()
print('===== best_fitness_history[0] (first gen) — should differ if PPS is real =====')
for problem in ['DF1', 'DF5']:
    for seed in range(2):  # just first 2 seeds
        de = data.get(('DE', problem, seed))
        pps = data.get(('PPS-DMOEA', problem, seed))
        if de and pps:
            de_h = de.get('best_fitness_history', [])[:5]
            pps_h = pps.get('best_fitness_history', [])[:5]
            de_bf = de.get('best_fitness_history', [])[-3:]
            pps_bf = pps.get('best_fitness_history', [])[-3:]
            print(f'{problem} seed={seed}:')
            print(f'  DE   first 5: {de_h}')
            print(f'  PPS  first 5: {pps_h}')
            print(f'  DE   last 3:  {de_bf}')
            print(f'  PPS  last 3:  {pps_bf}')
            print(f'  All identical: {de_h == pps_h and de_bf == pps_bf}')
            print()
