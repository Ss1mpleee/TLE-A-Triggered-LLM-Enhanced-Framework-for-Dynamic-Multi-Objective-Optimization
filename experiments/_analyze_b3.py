"""B3 analysis: per-action ablation results."""
import json
from collections import defaultdict
import numpy as np
from scipy.stats import wilcoxon

data = json.load(open(r'D:\新论文\实验\results\raw\exp3_uav_b3.json', encoding='utf-8'))
print(f"Total records: {len(data)}")

# Group by algo+n_uavs
gb = defaultdict(lambda: defaultdict(list))
for r in data:
    gb[r['algo']][r['n_uavs']].append(r['f1_value'])

# Compute mean for each (algo, n_uavs)
print()
print(f"{'Algo':<35} {'8-UAV':<12} {'16-UAV':<12} {'32-UAV':<12}")
print("-" * 75)
all_algos = ["DE", "DNSGA-II-A",
             "TLE-only-param", "TLE-only-archive_reset",
             "TLE-only-restart_top", "TLE-only-diversity_injection",
             "TLE-full"]
for algo in all_algos:
    if algo not in gb:
        continue
    row = f"{algo:<35}"
    for nu in [8, 16, 32]:
        vals = gb[algo].get(nu, [])
        if vals:
            row += f" {np.mean(vals):>5.1f}+/-{np.std(vals):<4.1f}"
        else:
            row += f" {'--':<10}"
    print(row)

print()
print("=== TLE-full vs each single-action variant (paired Wilcoxon) ===")
print(f"{'Variant':<35} {'8-UAV p':<12} {'16-UAV p':<12} {'32-UAV p':<12}")
print("-" * 75)
for variant in ["TLE-only-param", "TLE-only-archive_reset",
                "TLE-only-restart_top", "TLE-only-diversity_injection"]:
    row = f"{variant:<35}"
    for nu in [8, 16, 32]:
        full_d = {r['seed']: r['f1_value'] for r in data if r['algo'] == 'TLE-full' and r['n_uavs'] == nu}
        var_d = {r['seed']: r['f1_value'] for r in data if r['algo'] == variant and r['n_uavs'] == nu}
        common = sorted(set(full_d) & set(var_d))
        if len(common) >= 3:
            try:
                # Lower is better; test TLE-full < variant
                _, p = wilcoxon([full_d[s] for s in common],
                               [var_d[s] for s in common],
                               alternative='less')
                sig = "*" if p < 0.05 else "ns"
                row += f" {p:.4f} {sig:<4} "
            except Exception as e:
                row += f" {'--':<10}"
        else:
            row += f" {'--':<10}"
    print(row)

print()
print("=== TLE-full vs DE / DNSGA-II-A ===")
for baseline in ["DE", "DNSGA-II-A"]:
    print(f"\n{baseline}:")
    for nu in [8, 16, 32]:
        full_d = {r['seed']: r['f1_value'] for r in data if r['algo'] == 'TLE-full' and r['n_uavs'] == nu}
        base_d = {r['seed']: r['f1_value'] for r in data if r['algo'] == baseline and r['n_uavs'] == nu}
        common = sorted(set(full_d) & set(base_d))
        if len(common) >= 3:
            try:
                _, p = wilcoxon([full_d[s] for s in common],
                               [base_d[s] for s in common],
                               alternative='less')
                full_mean = np.mean([full_d[s] for s in common])
                base_mean = np.mean([base_d[s] for s in common])
                diff = (full_mean - base_mean) / base_mean * 100
                sig = "*" if p < 0.05 else "ns"
                print(f"  {nu}-UAV: TLE-full={full_mean:.1f}, {baseline}={base_mean:.1f}, "
                      f"diff={diff:+.2f}%, p={p:.4f} {sig}")
            except Exception as e:
                print(f"  {nu}-UAV: error {e}")