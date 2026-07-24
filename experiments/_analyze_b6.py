"""Quick analysis of B6 scalability results."""
import json
from collections import defaultdict
import numpy as np

data = json.load(open(r'D:\新论文\实验\results\raw\exp3_uav_b6.json', encoding='utf-8'))
print(f"Total records: {len(data)}")

# Group by algo+n_uavs, compute stats
gb = defaultdict(lambda: defaultdict(list))
for r in data:
    gb[r['algo']][r['n_uavs']].append(r['f1_value'])

print()
print(f"{'Algo':<25} {'Fleet':<8} {'n':<5} {'mean':<10} {'std':<10}")
print("-" * 60)
for algo in ['DE', 'DNSGA-II-A', 'TLE']:
    for nu in [4, 8, 16, 32]:
        if nu not in gb[algo]:
            continue
        vals = gb[algo][nu]
        print(f"{algo:<25} {nu:<8} {len(vals):<5} {np.mean(vals):<10.2f} {np.std(vals):<10.2f}")

print()
print("=== TLE 8-UAV vs 16-UAV vs 32-UAV (NEW data only, 5 seeds) ===")
for nu in [8, 16, 32]:
    tle = gb.get('TLE', {}).get(nu, [])
    de = gb.get('DE', {}).get(nu, [])
    dnsga = gb.get('DNSGA-II-A', {}).get(nu, [])
    if not tle or not de or not dnsga:
        continue
    print(f"{nu}-UAV (5 seeds):")
    print(f"  DE         mean={np.mean(de):.2f} +/- {np.std(de):.2f}")
    print(f"  DNSGA-II-A mean={np.mean(dnsga):.2f} +/- {np.std(dnsga):.2f}")
    print(f"  TLE        mean={np.mean(tle):.2f} +/- {np.std(tle):.2f}")
    print(f"  TLE vs DE:         {(np.mean(tle)-np.mean(de))/np.mean(de)*100:+.2f}%")
    print(f"  TLE vs DNSGA-II-A: {(np.mean(tle)-np.mean(dnsga))/np.mean(dnsga)*100:+.2f}%")

print()
print("=== Wilcoxon p-value: TLE vs DNSGA-II-A (paired by seed) ===")
from scipy.stats import wilcoxon
for nu in [8, 16, 32]:
    tle_d = {r['seed']: r['f1_value'] for r in data if r['algo'] == 'TLE' and r['n_uavs'] == nu}
    dnsga_d = {r['seed']: r['f1_value'] for r in data if r['algo'] == 'DNSGA-II-A' and r['n_uavs'] == nu}
    de_d = {r['seed']: r['f1_value'] for r in data if r['algo'] == 'DE' and r['n_uavs'] == nu}
    common = sorted(set(tle_d) & set(dnsga_d))
    if len(common) >= 3:
        try:
            # Lower is better; alternative: TLE < DNSGA
            _, p = wilcoxon([tle_d[s] for s in common], [dnsga_d[s] for s in common], alternative='less')
            print(f"  {nu}-UAV: TLE vs DNSGA-II-A n_paired={len(common)}, p={p:.4f} (TLE < DNSGA)")
        except Exception as e:
            print(f"  {nu}-UAV: error {e}")
    common2 = sorted(set(tle_d) & set(de_d))
    if len(common2) >= 3:
        try:
            _, p = wilcoxon([tle_d[s] for s in common2], [de_d[s] for s in common2], alternative='less')
            print(f"  {nu}-UAV: TLE vs DE         n_paired={len(common2)}, p={p:.4f} (TLE < DE)")
        except Exception as e:
            print(f"  {nu}-UAV: error {e}")