"""Compute new aggregate stats for paper."""
import json
import numpy as np
from collections import defaultdict

def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)

# Combine sec_main (DF1/DF5) + sec_pps_extended (DF2/DF3/DF7 PPS only)
# Plus we need DE/TLE/DE-LM-static-trigger on DF2/DF3/DF7 — those are NOT in sec_main
# We have them in exp2_dynamic_mo.json (3 seeds, max_gen=100, OLDER config)
# So for DF2/DF3/DF7 we only have 3-seed old data for non-PPS algos

sec_main = load(r'D:\新论文\实验\results\raw\sec_main.json')
sec_pps_ext = load(r'D:\新论文\实验\results\raw\sec_pps_extended.json')
sec_abl_v2 = load(r'D:\新论文\实验\results\raw\sec_ablation_v2.json')
sec_abl_v1 = load(r'D:\新论文\实验\results\raw\sec_ablation.json')

print('===== Main Table (5 seeds, 200 gen) — sec_main.json (DF1, DF5) =====')
by_ap = defaultdict(list)
by_inv = defaultdict(list)
for r in sec_main:
    if 'igd' in r and 'error' not in r:
        by_ap[(r['algo'], r['problem'])].append(r['igd'])
        by_inv[(r['algo'], r['problem'])].append(r['invocations'])

algos = ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'TLE']
probs = ['DF1', 'DF5']
print(f'{"Algo":30s} {"Problem":6s} {"IGD (mean ± std)":24s} {"Invocations (mean)"}')
for a in algos:
    for p in probs:
        vals = by_ap.get((a, p), [])
        invs = by_inv.get((a, p), [])
        if vals:
            print(f'{a:30s} {p:6s} {np.mean(vals):.4f} ± {np.std(vals):.4f}        {np.mean(invs):.1f}')

# Print ablation aggregated
print()
print('===== Ablation Table (5 seeds combined) =====')
abl_combined = sec_abl_v1 + sec_abl_v2
print(f'Combined ablation entries: {len(abl_combined)}')
by_vp = defaultdict(list)
for r in abl_combined:
    if 'variant' in r:
        by_vp[(r['variant'], r['problem'])].append(r['igd'])

variants = ['V0_TLE_full', 'V1_single_signal', 'V2_heuristic_budget', 'V3_no_llm']
for v in variants:
    for p in ['DF1', 'DF5']:
        vals = by_vp.get((v, p), [])
        if vals:
            print(f'{v:25s} {p:4s}: {np.mean(vals):.4f} ± {np.std(vals):.4f} (n={len(vals)})')

# Print PPS extended
print()
print('===== PPS-DMOEA extended (DF2/DF3/DF7, 5 seeds) =====')
by_p = defaultdict(list)
for r in sec_pps_ext:
    if 'igd' in r:
        by_p[r['problem']].append(r['igd'])
for p in ['DF2', 'DF3', 'DF7']:
    vals = by_p.get(p, [])
    if vals:
        print(f'PPS-DMOEA {p}: {np.mean(vals):.4f} ± {np.std(vals):.4f}')

# Pair with sec_main PPS for DF1/DF5
print()
print('===== Combined PPS-DMOEA (sec_main DF1/DF5 + sec_pps_ext DF2/3/7) =====')
pps_combined = []
for r in sec_main:
    if r.get('algo') == 'PPS-DMOEA' and 'igd' in r:
        pps_combined.append((r['problem'], r['igd']))
for r in sec_pps_ext:
    if 'igd' in r:
        pps_combined.append((r['problem'], r['igd']))

# Compare TLE vs PPS by problem
print()
print('===== TLE vs PPS (paired) =====')
for p in ['DF1', 'DF5']:
    tle_vals = [r['igd'] for r in sec_main if r.get('algo')=='TLE' and r.get('problem')==p and 'igd' in r]
    pps_vals = [r['igd'] for r in sec_main if r.get('algo')=='PPS-DMOEA' and r.get('problem')==p and 'igd' in r]
    if tle_vals and pps_vals:
        from scipy.stats import wilcoxon
        try:
            stat, pval = wilcoxon(tle_vals, pps_vals, alternative='less')
        except Exception:
            try:
                stat, pval = wilcoxon(tle_vals, pps_vals, alternative='two-sided')
            except Exception:
                pval = 1.0
        improvement = (np.mean(pps_vals) - np.mean(tle_vals)) / np.mean(pps_vals) * 100
        print(f'{p}: TLE {np.mean(tle_vals):.4f} ± {np.std(tle_vals):.4f}  vs  '
              f'PPS {np.mean(pps_vals):.4f} ± {np.std(pps_vals):.4f}  '
              f'(TLE {improvement:+.1f}%, p={pval:.3f})')
