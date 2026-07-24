"""
Auto-update Table 5 (UAV) and §5 UAV section from exp3_uav_v3.json
when the 30-seed experiment finishes.

This script reads exp3_uav_v3.json (which has 30 seeds × 5 algos × 2 fleets),
regenerates Table 5 with proper Wilcoxon p-values, and prints LaTeX snippets
that can be pasted into the paper.

Also writes the per-seed numeric breakdown to a SM-ready CSV.
"""
import json
import numpy as np
from collections import defaultdict
from scipy.stats import wilcoxon, mannwhitneyu
from pathlib import Path

V3 = Path(r'D:\新论文\实验\results\raw\exp3_uav_v3.json')

if not V3.exists():
    print(f'ERROR: {V3} not found. Background job may not have created output yet.')
    exit(1)

data = json.load(open(V3, encoding='utf-8'))
print(f'Loaded {len(data)} records from {V3}')

# Group by (algo, n_uavs)
gb = defaultdict(lambda: defaultdict(list))
for r in data:
    gb[r['algo']][r['n_uavs']].append(r['f1_value'])

# Summary
print('\n=== Summary table (mean ± std, n seeds) ===')
print(f'{"Algo":25s} {"4-UAV n":>10s} {"4-UAV f1":>15s} {"8-UAV n":>10s} {"8-UAV f1":>15s}')
algos = ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A', 'TLE']
for a in algos:
    n4 = len(gb[a][4])
    f4 = np.mean(gb[a][4]) if gb[a][4] else 0
    s4 = np.std(gb[a][4]) if gb[a][4] else 0
    n8 = len(gb[a][8])
    f8 = np.mean(gb[a][8]) if gb[a][8] else 0
    s8 = np.std(gb[a][8]) if gb[a][8] else 0
    print(f'{a:25s} {n4:>10d} {f4:>10.1f}±{s4:>4.1f} {n8:>10d} {f8:>10.1f}±{s8:>4.1f}')

# Paired Wilcoxon TLE vs each other
print('\n=== Paired Wilcoxon TLE > other (one-sided, paired by seed) ===')
for nu in [4, 8]:
    print(f'\n  n_uavs={nu}:')
    for a in algos:
        if a == 'TLE':
            continue
        # Pair by seed
        tle_d = {r['seed']: r['f1_value'] for r in data if r['algo']=='TLE' and r['n_uavs']==nu}
        oth_d = {r['seed']: r['f1_value'] for r in data if r['algo']==a and r['n_uavs']==nu}
        common = sorted(set(tle_d) & set(oth_d))
        if len(common) < 2:
            print(f'    TLE vs {a:25s}: only {len(common)} paired seeds, skip')
            continue
        tle_arr = np.array([tle_d[s] for s in common])
        oth_arr = np.array([oth_d[s] for s in common])
        try:
            w, p = wilcoxon(tle_arr, oth_arr, alternative='greater')
            diff = np.mean(tle_arr) - np.mean(oth_arr)
            pct = 100 * diff / np.mean(oth_arr) if np.mean(oth_arr) > 0 else 0
            sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
            print(f'    TLE vs {a:25s}: n={len(common):2d}, mean_diff={diff:+7.1f} ({pct:+5.1f}%), Wilcoxon p={p:.4f} {sig}')
        except Exception as e:
            print(f'    TLE vs {a}: {e}')

# Best per fleet
print('\n=== Best per fleet ===')
for nu in [4, 8]:
    means = {a: np.mean(gb[a][nu]) for a in algos if gb[a][nu]}
    if means:
        best = max(means, key=means.get)
        print(f'  {nu}-UAV: best is {best} (mean={means[best]:.1f})')
        for a in sorted(means, key=means.get, reverse=True):
            print(f'    {a:25s}: {means[a]:.1f}')

# Generate LaTeX Table 5 snippet
print('\n=== LaTeX Table 5 snippet (paste into main.tex) ===')
nu_best = {nu: max(algos, key=lambda a: np.mean(gb[a][nu]) if gb[a][nu] else -1) for nu in [4, 8]}
nu_p = {}
for nu in [4, 8]:
    nu_p[nu] = {}
    for a in algos:
        if a == 'TLE':
            continue
        tle_d = {r['seed']: r['f1_value'] for r in data if r['algo']=='TLE' and r['n_uavs']==nu}
        oth_d = {r['seed']: r['f1_value'] for r in data if r['algo']==a and r['n_uavs']==nu}
        common = sorted(set(tle_d) & set(oth_d))
        if len(common) >= 2:
            try:
                _, p = wilcoxon([tle_d[s] for s in common], [oth_d[s] for s in common], alternative='greater')
                nu_p[nu][a] = p
            except:
                nu_p[nu][a] = 1.0

print(r'\begin{tabular}{lcccc}')
print(r'\toprule')
print(r'Algorithm & 4-UAV $f_1$ & 4-UAV $p$ vs.\ DE & 8-UAV $f_1$ & 8-UAV $p$ vs.\ DE \\')
print(r'\midrule')
for a in algos:
    cells = [a]
    for nu in [4, 8]:
        vals = gb[a][nu]
        if vals:
            m, s = np.mean(vals), np.std(vals)
            cell = f'{m:.1f} $\\pm$ {s:.1f}'
            if a == nu_best[nu]:
                cell = r'\textbf{' + cell + r'}'
            cells.append(cell)
        else:
            cells.append('--')
        if a != 'DE':
            p = nu_p[nu].get(a, 1.0)
            cells.append(f'{p:.4f}')
        else:
            cells.append('--')
    print(' & '.join(cells) + r' \\')
print(r'\bottomrule')
print(r'\end{tabular}')