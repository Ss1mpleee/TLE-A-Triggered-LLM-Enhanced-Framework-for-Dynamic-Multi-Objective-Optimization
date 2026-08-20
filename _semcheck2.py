"""semcheck2: extract ground-truth values from raw data for all paper claims."""
import json
import numpy as np
from collections import defaultdict

ROOT = r'results\raw'

# ---------- load ----------
with open(f'{ROOT}\\sec_main_v3.json', encoding='utf-8') as f:
    main = json.load(f)            # 2520 runs, main n=30 experiment
with open(f'{ROOT}\\exp6_cross_llm_n14.json', encoding='utf-8') as f:
    cross = json.load(f)           # 1260 runs, 3 LLMs x 14 problems x 30 seeds
with open(f'{ROOT}\\exp7_ablation_combined.json', encoding='utf-8') as f:
    abl = json.load(f)             # 1680 runs, 4 versions x 14 problems x 30 seeds
with open(f'{ROOT}\\exp3_uav_v3.json', encoding='utf-8') as f:
    uav = json.load(f)             # 300 runs
with open(f'{ROOT}\\exp4_moeadd.json', encoding='utf-8') as f:
    moeadd = json.load(f)
with open(f'{ROOT}\\sec_ablation_v2.json', encoding='utf-8') as f:
    abl2 = json.load(f)            # 40 runs, 4 versions x 2 problems x 5 seeds (V0_TLE_full etc)
with open(f'{ROOT}\\exp_trigger_threshold.json', encoding='utf-8') as f:
    trig_th = json.load(f)

# ---------- helpers ----------
def get(records, **kw):
    for k, v in kw.items():
        if callable(v):
            records = [r for r in records if v(r.get(k))]
        else:
            records = [r for r in records if r.get(k) == v]
    return records

def mean(xs):
    return float(np.mean(xs)) if xs else float('nan')
def std(xs):
    return float(np.std(xs)) if xs else float('nan')
def median(xs):
    return float(np.median(xs)) if xs else float('nan')

# ---------- 1. MAIN (2520) ----------
# Filter: exclude MOEA/DD runs with catastrophic IGD > 1e3 (the paper's filter convention)
def filter_main(rs, algo, problem):
    out = []
    for r in rs:
        if r['algo'] != algo or r['problem'] != problem:
            continue
        # Per paper: IGD values > 1000 are "catastrophic", excluded from table cell means
        # But we need to check the raw IGD too
        if r.get('igd', 0) is None:
            continue
        out.append(r)
    return out

print('='*60)
print('SECTION A: Main 6-algorithm x 14-problem x 30-seed (sec_main_v3)')
print('='*60)

# Per-algorithm, per-problem
ALGOS = ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A', 'MOEA/DD', 'TLE']
PROBLEMS = [f'DF{i}' for i in range(1, 15)]

# IGD table
print('\n--- IGD per (algorithm, problem), n=30, filter IGD<1e3 ---')
for algo in ALGOS:
    for prob in PROBLEMS:
        rs = filter_main(main, algo, prob)
        igds_raw = [r['igd'] for r in rs if r.get('igd') is not None and r['igd'] < 1e3]
        igds_all = [r['igd'] for r in rs if r.get('igd') is not None]
        n_cat = len(igds_all) - len(igds_raw)
        if igds_raw:
            print(f'  {algo:24s} {prob:5s} n={len(igds_raw):2d} cat={n_cat:2d} mean={mean(igds_raw):.4f} median={median(igds_raw):.4f} min={min(igds_raw):.4f} max={max(igds_raw):.4f}')
        else:
            print(f'  {algo:24s} {prob:5s} all catastrophic ({n_cat}/30)')

# Mean invocations
print('\n--- Mean LLM invocations ---')
for algo in ALGOS:
    invs = [r['invocations'] for r in main if r['algo'] == algo and r.get('invocations') is not None]
    if invs:
        print(f'  {algo:24s} mean_inv={mean(invs):.2f} median_inv={median(invs):.2f} min={min(invs)} max={max(invs)}')

# Per-problem mean invocations for TLE
print('\n--- TLE per-problem invocations ---')
for prob in PROBLEMS:
    rs = [r for r in main if r['algo'] == 'TLE' and r['problem'] == prob]
    invs = [r['invocations'] for r in rs]
    if invs:
        # paper claims 9.7% DF8 / 38.9% DF11 etc
        pct = mean(invs) / 200 * 100
        print(f'  {prob:5s} mean={mean(invs):.2f} median={median(invs):.2f} pct={pct:.2f}%')

# DE-LM-static per-problem
print('\n--- DE-LM-static per-problem invocations ---')
for prob in PROBLEMS:
    rs = [r for r in main if r['algo'] == 'DE-LM-static-trigger' and r['problem'] == prob]
    invs = [r['invocations'] for r in rs]
    if invs:
        pct = mean(invs) / 200 * 100
        print(f'  {prob:5s} mean={mean(invs):.2f} pct={pct:.2f}%')
