"""semcheck4: cross-LLM, ablation, UAV data validation."""
import json
import numpy as np
from collections import defaultdict

ROOT = r'results\raw'

with open(f'{ROOT}\\exp6_cross_llm_n14.json', encoding='utf-8') as f:
    cross = json.load(f)
with open(f'{ROOT}\\exp7_ablation_combined.json', encoding='utf-8') as f:
    abl = json.load(f)
with open(f'{ROOT}\\exp3_uav_v3.json', encoding='utf-8') as f:
    uav = json.load(f)
with open(f'{ROOT}\\sec_ablation_v2.json', encoding='utf-8') as f:
    abl2 = json.load(f)

print('='*60)
print('SECTION B: Cross-LLM (3 LLMs x 14 problems x 30 seeds = 1260)')
print('='*60)

# Group by model, problem
by_mp = defaultdict(list)
for r in cross:
    by_mp[(r['model'], r['prob'])].append(r['igd'])

MODELS = ['qwen2.5:7b', 'qwen3.5:9b', 'carstenuhlig/omnicoder-9b:q8_0']
PROBS = [f'DF{i}' for i in range(1, 15)]

print('\n--- Cross-LLM IGD mean per (model, prob), n=30 (no filter) ---')
for m in MODELS:
    print(f'  {m}:')
    means = []
    for p in PROBS:
        igds = by_mp.get((m, p), [])
        if igds:
            means.append(np.mean(igds))
            print(f'    {p:5s} mean={np.mean(igds):.4f} median={np.median(igds):.4f} n={len(igds)}')
    print(f'    MEAN of 14 means = {np.mean(means):.4f}')

# DF2 catastrophic check
print('\n--- DF2 catastrophic seed count per LLM (IGD > 1000) ---')
for m in MODELS:
    igds = by_mp.get((m, 'DF2'), [])
    cats = [g for g in igds if g > 1000]
    print(f'  {m:18s} n_total={len(igds):2d} n_cat={len(cats):2d}')
    if cats:
        print(f'      cat range: {min(cats):.2f} - {max(cats):.2f}')

# byte-identical check
print('\n--- Byte-identical check between qwen3.5 and omnicoder ---')
for p in PROBS:
    a = sorted(by_mp.get(('qwen3.5:9b', p), []))
    b = sorted(by_mp.get(('carstenuhlig/omnicoder-9b:q8_0', p), []))
    if a and b and a == b:
        print(f'  {p}: BYTE-IDENTICAL')
    elif a and b:
        # max diff
        diff = max(abs(x - y) for x, y in zip(a, b))
        print(f'  {p}: max diff = {diff:.4f}')

# DF14 detail
print('\n--- DF14 detail per LLM ---')
for m in MODELS:
    igds = sorted(by_mp.get((m, 'DF14'), []))
    outliers = [g for g in igds if g > 0.05]
    print(f'  {m:18s} min={min(igds):.4f} max={max(igds):.4f} mean={np.mean(igds):.4f} median={np.median(igds):.4f} n_outlier={len(outliers)}')

# 3-objective DF11 detail
print('\n--- DF11 detail per LLM ---')
for m in MODELS:
    igds = sorted(by_mp.get((m, 'DF11'), []))
    print(f'  {m:18s} min={min(igds):.4f} max={max(igds):.4f} mean={np.mean(igds):.4f} median={np.median(igds):.4f}')

print('\n--- DF5 detail (paper: 4.1x reduction for Qwen-2.5-7B) ---')
for m in MODELS:
    igds = sorted(by_mp.get((m, 'DF5'), []))
    print(f'  {m:18s} min={min(igds):.4f} max={max(igds):.4f} mean={np.mean(igds):.4f} median={np.median(igds):.4f}')

# Paper: 1.25x and 1.28x for DF1 and DF7
print('\n--- DF1, DF7 (paper: 1.25x, 1.28x IGD increase) ---')
for p in ['DF1', 'DF7']:
    print(f'  {p}:')
    for m in MODELS:
        igds = by_mp.get((m, p), [])
        print(f'    {m:18s} mean={np.mean(igds):.4f} median={np.median(igds):.4f}')

# DF8 - paper says byte-identical claim
print('\n--- DF8 detail ---')
for m in MODELS:
    igds = sorted(by_mp.get((m, 'DF8'), []))
    print(f'  {m:18s} min={min(igds):.4f} max={max(igds):.4f} mean={np.mean(igds):.4f} median={np.median(igds):.4f}')

print('\n' + '='*60)
print('SECTION C: Ablation 4x14x30=1680')
print('='*60)

by_vp = defaultdict(list)
for r in abl:
    by_vp[(r['version'], r['problem'])].append(r['igd'])
    by_vp[(r['version'], r['problem']) + ('inv',)].append(r['invocations'])

VERSIONS = ['V0_baseline', 'V1_entropy', 'V2_double', 'V3_triple']
print('\n--- Ablation IGD per (version, prob) ---')
for v in VERSIONS:
    print(f'  {v}:')
    means = []
    inv_means = []
    for p in PROBS:
        igds = by_vp.get((v, p), [])
        invs = by_vp.get((v, p) + ('inv',), [])
        if igds:
            means.append(np.mean(igds))
            inv_means.append(np.mean(invs))
            print(f'    {p:5s} mean={np.mean(igds):.4f} inv={np.mean(invs):.2f}')

# Per-version overall mean
print('\n--- Per-version overall (mean of 14 means) ---')
for v in VERSIONS:
    means = [np.mean(by_vp.get((v, p), [])) for p in PROBS if by_vp.get((v, p))]
    inv_means = [np.mean(by_vp.get((v, p) + ('inv',), [])) for p in PROBS if by_vp.get((v, p))]
    print(f'  {v:14s} 14-mean_igd={np.mean(means):.4f} 14-mean_inv={np.mean(inv_means):.2f} median_inv={np.median(inv_means):.2f}')

# DF1 V0 vs V3 specifically (paper: 49.4% gap)
print('\n--- DF1 V0 vs V3 (paper: 49.4% gap) ---')
v0_df1 = sorted(by_vp.get(('V0_baseline', 'DF1'), []))
v3_df1 = sorted(by_vp.get(('V3_triple', 'DF1'), []))
print(f'  V0: mean={np.mean(v0_df1):.4f} median={np.median(v0_df1):.4f}')
print(f'  V3: mean={np.mean(v3_df1):.4f} median={np.median(v3_df1):.4f}')
gap = (np.median(v0_df1) - np.median(v3_df1)) / np.median(v3_df1) * 100
print(f'  Gap (V0 vs V3 median): {gap:.1f}%')

# DF4 lock
print('\n--- DF4 lock (paper: V0 median=0.7633 on all 30 seeds) ---')
for v in VERSIONS:
    igds = by_vp.get((v, 'DF4'), [])
    print(f'  {v:14s} median={np.median(igds):.4f} min={min(igds):.4f} max={max(igds):.4f} unique={len(set(round(g, 4) for g in igds))}')

print('\n' + '='*60)
print('SECTION D: UAV (300 runs: 5 algos x 4 fleet sizes x 15 seeds)')
print('='*60)

# Group UAV
by_as = defaultdict(list)
for r in uav:
    by_as[(r['algo'], r['n_uavs'])].append(r)

ALGOS_U = ['DE', 'DNSGA-II-A', 'TLE']
print('\n--- UAV f1 by algo x n_uavs ---')
for n_uav in [4, 8, 16, 32]:
    print(f'  {n_uav}-UAV:')
    for a in sorted(set(r['algo'] for r in uav)):
        rs = by_as.get((a, n_uav), [])
        f1 = [r['f1_value'] for r in rs if r.get('f1_value') is not None]
        if f1:
            print(f'    {a:20s} n={len(f1):2d} mean={np.mean(f1):.2f} std={np.std(f1):.2f} median={np.median(f1):.2f}')

# Check Wilcoxon p-values for TLE vs DNSGA-II-A
print('\n--- TLE vs DNSGA-II-A (paper: 21.2% / 20.4% / 19.0% gap) ---')
from scipy.stats import wilcoxon
for n_uav in [4, 8, 16, 32]:
    tle = sorted([r['f1_value'] for r in by_as.get(('TLE', n_uav), []) if r.get('f1_value') is not None])
    dn = sorted([r['f1_value'] for r in by_as.get(('DNSGA-II-A', n_uav), []) if r.get('f1_value') is not None])
    if tle and dn:
        n = min(len(tle), len(dn))
        try:
            stat, p = wilcoxon(tle[:n], dn[:n], alternative='less')
        except Exception as e:
            p = -1
        gap = (np.mean(dn) - np.mean(tle)) / np.mean(dn) * 100
        print(f'  {n_uav}-UAV: n_tle={len(tle):2d} n_dn={len(dn):2d} TLE={np.mean(tle):.2f} DNSGA={np.mean(dn):.2f} gap={gap:.2f}% p={p:.4f}')
