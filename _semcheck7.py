import json, numpy as np
from collections import defaultdict
with open(r'results\raw\sec_main_v3.json', encoding='utf-8') as f:
    main = json.load(f)
by_a = defaultdict(lambda: {'inv': [], 'igd': []})
for r in main:
    if 'invocations' in r and r.get('igd') is not None:
        by_a[r['algo']]['inv'].append(r['invocations'])
        by_a[r['algo']]['igd'].append(r['igd'])

print('per-algo summary (filter IGD<1e3, all 14 problems):')
for algo in ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A', 'MOEA/DD', 'TLE']:
    inv = by_a[algo]['inv']
    igds = [g for g in by_a[algo]['igd'] if g < 1e3]
    overall_median = np.median(igds) if igds else 0
    overall_mean = np.mean(igds) if igds else 0
    print(f'  {algo:24s} inv_mean={np.mean(inv):.2f} IGD_overall_median={overall_median:.4f} overall_mean={overall_mean:.4f}')

# IGD / 1000 calls based on overall median
print()
print('Cost-norm based on overall median IGD:')
for algo in ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A', 'MOEA/DD', 'TLE']:
    inv = by_a[algo]['inv']
    igds = [g for g in by_a[algo]['igd'] if g < 1e3]
    overall_median = np.median(igds) if igds else 0
    inv_mean = np.mean(inv)
    cost_norm = overall_median * 1000 / max(inv_mean, 1) if inv_mean > 0 else overall_median
    print(f'  {algo:24s} cost_norm_1000={cost_norm:.2f}')
