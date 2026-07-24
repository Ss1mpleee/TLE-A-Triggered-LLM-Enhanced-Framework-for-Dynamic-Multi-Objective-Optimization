"""Summarize sec_main_v2.json / sec_ablation_v2.json / exp3_uav_v2.json results."""
import json
import numpy as np
from collections import defaultdict
from pathlib import Path

RAW = Path(r'D:\新论文\实验\results\raw')

def load(name):
    p = RAW / name
    if not p.exists():
        return None
    return json.load(open(p, encoding='utf-8'))

def stats(rows, key):
    if not rows:
        return None
    vals = [r[key] for r in rows if key in r and r.get(key) is not None]
    vals = [v for v in vals if np.isfinite(v)]
    if not vals:
        return None
    return np.mean(vals), np.std(vals), len(vals)

# === Main DMO ===
main = load('sec_main_v2.json')
print('=' * 70)
print('MAIN DMO (5 algos × 5 probs × 5 seeds = 125 runs)')
print('=' * 70)
if main:
    by_ap = defaultdict(list)
    for r in main:
        if 'igd' in r and np.isfinite(r.get('igd', float('nan'))):
            by_ap[(r['algo'], r['problem'])].append(r['igd'])
    algos = ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A', 'TLE']
    probs = ['DF1', 'DF2', 'DF3', 'DF5', 'DF7']
    print(f'{"Algo":22s} {"Prob":5s} {"IGD (mean±std)":18s} {"n"}')
    for a in algos:
        for p in probs:
            vals = by_ap.get((a, p), [])
            if vals:
                print(f'{a:22s} {p:5s} {np.mean(vals):.4f} ± {np.std(vals):.4f}    {len(vals)}')

# === Ablation ===
abl = load('sec_ablation_v2.json')
print()
print('=' * 70)
print('ABLATION (V0-V3 × DF1+DF5 × 5 seeds)')
print('=' * 70)
if abl:
    by_vp = defaultdict(list)
    for r in abl:
        if 'igd' in r and np.isfinite(r.get('igd', float('nan'))):
            by_vp[(r['variant'], r['problem'])].append(r['igd'])
    variants = ['V0_TLE_full', 'V1_single_signal', 'V2_heuristic_budget', 'V3_no_llm']
    for v in variants:
        for p in ['DF1', 'DF5']:
            vals = by_vp.get((v, p), [])
            if vals:
                print(f'{v:25s} {p:4s}: {np.mean(vals):.4f} ± {np.std(vals):.4f} (n={len(vals)})')

# === UAV ===
uav = load('exp3_uav_v2.json')
print()
print('=' * 70)
print('UAV (5 algos × 5 seeds × {4, 8} UAVs)')
print('=' * 70)
if uav:
    by_an = defaultdict(lambda: defaultdict(list))
    for r in uav:
        if 'f1_value' in r:
            by_an[(r['algo'], r.get('n_uavs'))]['value'].append(r['f1_value'])
            by_an[(r['algo'], r.get('n_uavs'))]['time'].append(r['f2_response_time'])
            by_an[(r['algo'], r.get('n_uavs'))]['batt'].append(r['f3_battery'])
            by_an[(r['algo'], r.get('n_uavs'))]['inv'].append(r.get('invocations', 0))
    algos = sorted(set(r['algo'] for r in uav if 'algo' in r))
    nuavs = sorted(set(r.get('n_uavs') for r in uav if 'n_uavs' in r))
    for nu in nuavs:
        print(f'\n  n_uavs={nu}:')
        print(f'  {"Algo":22s} {"Value (↑)":14s} {"Time (↓)":14s} {"Batt (↑)":14s} {"LLM calls":10s}')
        for a in algos:
            d = by_an[(a, nu)]
            if d['value']:
                inv_str = f"{np.mean(d['inv']):.1f}"
                print(f'  {a:22s} {np.mean(d["value"]):6.1f}±{np.std(d["value"]):4.1f}    '
                      f'{np.mean(d["time"]):6.1f}±{np.std(d["time"]):4.1f}    '
                      f'{np.mean(d["batt"]):6.1f}±{np.std(d["batt"]):4.1f}    {inv_str}')
