"""semcheck8: Comprehensive numerical validation for all paper claims."""
import json
import numpy as np
from collections import defaultdict

print('='*70)
print('COMPREHENSIVE PAPER CLAIM vs RAW DATA VALIDATION')
print('='*70)

# Load all data
with open(r'results\raw\sec_main_v3.json', encoding='utf-8') as f:
    main = json.load(f)
with open(r'results\raw\exp6_cross_llm_n14.json', encoding='utf-8') as f:
    cross = json.load(f)
with open(r'results\raw\exp7_ablation_combined.json', encoding='utf-8') as f:
    abl = json.load(f)
with open(r'results\raw\exp3_uav_v3.json', encoding='utf-8') as f:
    uav = json.load(f)

def get_main_means(algo, prob_list, filter_cat=True):
    means = []
    for prob in prob_list:
        rs = [r for r in main if r['algo']==algo and r['problem']==prob]
        if filter_cat:
            igds = [r['igd'] for r in rs if r.get('igd') is not None and r['igd'] < 1e3]
        else:
            igds = [r['igd'] for r in rs if r.get('igd') is not None]
        if igds:
            means.append(np.mean(igds))
    return means

def get_overall_median(algo, filter_cat=True):
    all_igds = []
    for r in main:
        if r['algo'] == algo and r.get('igd') is not None:
            if filter_cat and r['igd'] >= 1e3:
                continue
            all_igds.append(r['igd'])
    return np.median(all_igds) if all_igds else 0

def get_14prob_mean_inv(algo):
    invs = [r['invocations'] for r in main if r['algo']==algo and r.get('invocations') is not None]
    return np.mean(invs) if invs else 0

# === Tab:igd (DF1-DF7) ===
print('\n## TAB:IGD - 7-problem means (filter<1e3)')
ALGOS = ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A', 'MOEA/DD', 'TLE']
PROBS_7 = ['DF1', 'DF2', 'DF3', 'DF4', 'DF5', 'DF6', 'DF7']
PAPER_MEAN = {'DE': 0.6098, 'DE-LM-static-trigger': 3.7658, 'PPS-DMOEA': 1.8097,
              'DNSGA-II-A': 0.4924, 'MOEA/DD': 0.4412, 'TLE': 0.8030}
for algo in ALGOS:
    if algo == 'MOEA/DD':
        # 4 non-cat problems
        means = [np.mean([r['igd'] for r in main if r['algo']==algo and r['problem']==p and r.get('igd', 0) < 1e3]) for p in ['DF1','DF3','DF5','DF7']]
    else:
        means = get_main_means(algo, PROBS_7, filter_cat=True)
    paper = PAPER_MEAN[algo]
    actual = np.mean(means) if algo != 'MOEA/DD' else np.mean(means)
    status = 'OK' if abs(actual - paper) < 0.001 else 'X'
    print(f'  {status} {algo:24s} actual={actual:.4f}  paper={paper:.4f}')

# === IGD/1000 calls ===
print('\n## TAB:IGD - IGD per 1000 calls')
PAPER_1000 = {'DE': 0.61, 'DE-LM-static-trigger': 226.86, 'PPS-DMOEA': 1.81,
              'DNSGA-II-A': 0.49, 'MOEA/DD': 0.44, 'TLE': 20.81}
for algo in ALGOS:
    if algo == 'MOEA/DD':
        mean_igd = np.mean([r['igd'] for r in main if r['algo']==algo and r.get('igd', 0) < 1e3])
    else:
        means = get_main_means(algo, PROBS_7, filter_cat=True)
        mean_igd = np.mean(means)
    inv = get_14prob_mean_inv(algo)
    actual_1000 = mean_igd * 1000 / max(inv, 1) if inv > 0 else mean_igd
    paper = PAPER_1000[algo]
    status = 'OK' if abs(actual_1000 - paper) < 0.1 else 'X'
    print(f'  {status} {algo:24s} actual={actual_1000:.2f}  paper={paper:.2f}')

# === Cost-qual 2.34× ===
print('\n## Cost-qual 2.34× (overall median based)')
for algo in ['TLE', 'DE-LM-static-trigger']:
    om = get_overall_median(algo)
    inv = get_14prob_mean_inv(algo)
    cn = om * 1000 / inv
    print(f'  {algo:24s} overall_median={om:.4f} inv={inv:.2f} cost_norm_1000={cn:.2f}')
print('  2.34× = 44.18/18.88 =', 44.18/18.88)

# === Trigger rate 9.7-38.9%, mean 19.3% ===
print('\n## TLE trigger rate (DF8=9.7%, DF11=38.9%, mean=19.3%)')
tle_inv = {}
for prob in ['DF1','DF2','DF3','DF4','DF5','DF6','DF7','DF8','DF9','DF10','DF11','DF12','DF13','DF14']:
    rs = [r for r in main if r['algo']=='TLE' and r['problem']==prob]
    invs = [r['invocations'] for r in rs]
    if invs:
        tle_inv[prob] = np.mean(invs)
        print(f'  {prob}: mean={np.mean(invs):.2f} pct={np.mean(invs)/200*100:.2f}%')
all_pct = [v/200*100 for v in tle_inv.values()]
print(f'  min={min(all_pct):.1f}%  max={max(all_pct):.1f}%  mean={np.mean(all_pct):.1f}%')
sorted_pct = sorted(all_pct)
n = len(sorted_pct)
q1 = sorted_pct[int(n*0.25)]
q3 = sorted_pct[int(n*0.75)]
print(f'  IQR: [{q1:.1f}%, {q3:.1f}%]')

# === Cross-LLM DF2 catastrophic ===
print('\n## Cross-LLM DF2 catastrophic (Qwen-2.5-7B)')
qwen_df2 = sorted([r['igd'] for r in cross if r['model']=='qwen2.5:7b' and r['prob']=='DF2'])
cats = [g for g in qwen_df2 if g > 1000]
print(f'  Total seeds: {len(qwen_df2)}')
print(f'  Catastrophic (>1e3): {len(cats)} seeds, range [{min(cats):.2f}, {max(cats):.2f}]')
print(f'  Non-cat range: [{min(g for g in qwen_df2 if g <= 1000):.4f}, {max(g for g in qwen_df2 if g <= 1000):.4f}]')
medium = [g for g in qwen_df2 if 1 < g < 1000]
print(f'  Medium-failure (1 < g < 1000): {len(medium)} seeds, values={[round(g,2) for g in medium]}')

# === Cross-LLM DF14 outliers ===
print('\n## Cross-LLM DF14 outliers')
for model in ['qwen2.5:7b', 'qwen3.5:9b', 'carstenuhlig/omnicoder-9b:q8_0']:
    igds = sorted([r['igd'] for r in cross if r['model']==model and r['prob']=='DF14'])
    outliers = [g for g in igds if g > 0.05]
    print(f'  {model:50s} mean={np.mean(igds):.4f} outliers={len(outliers)}: {[round(g, 3) for g in outliers]}')

# === Byte-identical check ===
print('\n## Byte-identical problems (qwen3.5 == omnicoder)')
for p in ['DF1','DF2','DF3','DF4','DF5','DF6','DF7','DF8','DF9','DF10','DF11','DF12','DF13','DF14']:
    a = sorted([r['igd'] for r in cross if r['model']=='qwen3.5:9b' and r['prob']==p])
    b = sorted([r['igd'] for r in cross if r['model']=='carstenuhlig/omnicoder-9b:q8_0' and r['prob']==p])
    if a == b:
        print(f'  {p}: BYTE-IDENTICAL')

# === DF1 T0 vs T3 (5 seeds) ===
print('\n## V0 vs V3 5-seed DF1 gap (49.4%)')
with open(r'results\raw\sec_ablation_v2.json', encoding='utf-8') as f:
    abl2 = json.load(f)
v0_df1 = sorted([r['igd'] for r in abl2 if r['variant']=='V0_TLE_full' and r['problem']=='DF1'])
v3_df1 = sorted([r['igd'] for r in abl2 if r['variant']=='V3_no_llm' and r['problem']=='DF1'])
print(f'  V0 (TLE): n={len(v0_df1)} mean={np.mean(v0_df1):.4f}')
print(f'  V3 (no LLM): n={len(v3_df1)} mean={np.mean(v3_df1):.4f}')
print(f'  Gap (V3 vs V0): {(np.mean(v0_df1) - np.mean(v3_df1))/np.mean(v0_df1)*100:.1f}%')

# === Wilcoxon p-values check ===
print('\n## Wilcoxon p-values (key claims)')
# DF5: T3 vs T0 p=0.0001, win
# DF10: T3 vs T0 p=0.0000, win
# DF11: T3 vs T0 p=0.0000, win
# These are hardcoded in paper table; source data is in stats_ablation_crossllm.py

# === UAV TLE vs DNSGA-II-A ===
print('\n## UAV TLE vs DNSGA-II-A gap (21.2/20.4/19.0%)')
for n_uav in [4, 8, 16, 32]:
    tle = sorted([r['f1_value'] for r in uav if r['algo']=='TLE' and r['n_uavs']==n_uav])
    dn = sorted([r['f1_value'] for r in uav if r['algo']=='DNSGA-II-A' and r['n_uavs']==n_uav])
    if tle and dn:
        gap = (np.mean(dn) - np.mean(tle))/np.mean(dn)*100
        print(f'  {n_uav}-UAV: TLE={np.mean(tle):.2f} DNSGA={np.mean(dn):.2f} gap={gap:.1f}%')

print('\n' + '='*70)
print('VALIDATION COMPLETE')
print('='*70)
