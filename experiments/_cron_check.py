"""Cron progress check for UAV 30-seed experiment.
Reads v3.json (true progress) and reports it.
"""
import json
import os
import time
import numpy as np
from collections import defaultdict
from scipy.stats import wilcoxon

V3 = r'D:\新论文\实验\results\raw\exp3_uav_v3.json'
LOG = r'D:\新论文\实验\results\raw\uav30.log'

# Read v3.json (true progress)
data = json.load(open(V3, encoding='utf-8'))
total = len(data)
new_runs_set = {(r['algo'], r['n_uavs'], r['seed']) for r in data if r['seed'] >= 5}
new_runs = len(new_runs_set)

# Per-algo breakdown
gb = defaultdict(lambda: defaultdict(list))
for r in data:
    if r['seed'] >= 5:
        gb[r['algo']][r['n_uavs']].append(r['seed'])

# Log file mtime
log_mtime = os.path.getmtime(LOG)
log_mtime_str = time.strftime("%H:%M:%S", time.localtime(log_mtime))

# Current TLE 8-UAV vs DE 8-UAV paired Wilcoxon
tle_8_d = {r['seed']: r['f1_value'] for r in data if r['algo']=='TLE' and r['n_uavs']==8}
de_8_d = {r['seed']: r['f1_value'] for r in data if r['algo']=='DE' and r['n_uavs']==8}
common = sorted(set(tle_8_d) & set(de_8_d))

p_val = None
mean_tle = mean_de = mean_diff = pct_diff = None
if len(common) >= 3:
    tle_arr = np.array([tle_8_d[s] for s in common])
    de_arr = np.array([de_8_d[s] for s in common])
    try:
        w, p_val = wilcoxon(tle_arr, de_arr, alternative='greater')
        mean_tle = np.mean(tle_arr)
        mean_de = np.mean(de_arr)
        mean_diff = mean_tle - mean_de
        pct_diff = 100 * mean_diff / mean_de if mean_de > 0 else 0
    except Exception as e:
        p_val = f'err: {e}'

# Print report
print(f'=== UAV 30-seed Progress Report ===')
print(f'Total records in v3: {total} (50 from v2 + {total-50} new)')
print(f'NEW runs done: {new_runs} / 250 = {100*new_runs/250:.1f}%')
print(f'Log last modified: {log_mtime_str} (log buffering may be stale; trust v3.json)')
print()
print(f'=== Per-algo NEW seeds ===')
for a in sorted(gb.keys()):
    for nu in sorted(gb[a].keys()):
        print(f'  {a:25s} n_uavs={nu}: {len(gb[a][nu])} new seeds')

print()
print(f'=== TLE 8-UAV vs DE 8-UAV (n_paired = {len(common)}) ===')
if p_val is None:
    print(f'  Only {len(common)} paired seeds; need >=3 for Wilcoxon')
elif isinstance(p_val, float):
    sig = '***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'ns'
    print(f'  TLE mean = {mean_tle:.1f}, DE mean = {mean_de:.1f}')
    print(f'  diff = {mean_diff:+.1f} ({pct_diff:+.1f}%)')
    print(f'  Wilcoxon one-sided p = {p_val:.4f} {sig}')
else:
    print(f'  p_value error: {p_val}')

# ETA
elapsed_min = (time.time() - os.path.getmtime(V3))  # since last v3 write
# Total wall clock since start
import subprocess
# Get process start time
try:
    ps = subprocess.run(['powershell', '-Command', '(Get-Process -Id 13788 -ErrorAction SilentlyContinue).StartTime'], capture_output=True, text=True, timeout=5, encoding='utf-8', errors='ignore')
    start_str = ps.stdout.strip() if ps.stdout else 'unknown'
except Exception:
    start_str = 'unknown'
print()
print(f'=== ETA ===')
print(f'Process started: {start_str}')
# Estimate rate from known data: 81 runs in ~96 min (since 09:05)
# But DE-LM-static is slower (~145s) than DE (~35s)
# So estimate: weighted avg of remaining algo types
remaining = 250 - new_runs
# Per-algo remaining
remaining_de = max(0, 25 - len(gb.get('DE', {}).get(4, [])))
remaining_de_8 = max(0, 25 - len(gb.get('DE', {}).get(8, [])))
remaining_static_4 = max(0, 25 - len(gb.get('DE-LM-static-trigger', {}).get(4, [])))
remaining_static_8 = max(0, 25 - len(gb.get('DE-LM-static-trigger', {}).get(8, [])))
remaining_pps = max(0, 50 - (len(gb.get('PPS-DMOEA', {}).get(4, [])) + len(gb.get('PPS-DMOEA', {}).get(8, []))))
remaining_dnsga = max(0, 50 - (len(gb.get('DNSGA-II-A', {}).get(4, [])) + len(gb.get('DNSGA-II-A', {}).get(8, []))))
remaining_tle_4 = max(0, 25 - len(gb.get('TLE', {}).get(4, [])))
remaining_tle_8 = max(0, 25 - len(gb.get('TLE', {}).get(8, [])))

# Per-algo time estimate (from observed rates)
time_per = {
    'DE': 35, 'DE-LM-static-trigger': 145, 'PPS-DMOEA': 35,
    'DNSGA-II-A': 35, 'TLE': 100,
}
eta_sec = (remaining_de + remaining_de_8) * 35 + \
          (remaining_static_4 + remaining_static_8) * 145 + \
          remaining_pps * 35 + remaining_dnsga * 35 + \
          (remaining_tle_4 + remaining_tle_8) * 100
eta_min = eta_sec / 60

print(f'Per-algo remaining: DE={remaining_de+remaining_de_8}, static={remaining_static_4+remaining_static_8}, PPS={remaining_pps}, DNSGA={remaining_dnsga}, TLE={remaining_tle_4+remaining_tle_8}')
print(f'ETA: {eta_min:.0f} min = {eta_min/60:.1f} hours (weighted by per-algo time)')

# Status string
if new_runs == 250:
    print()
    print('=== EXPERIMENT COMPLETE ===')
    print('Run experiments/_post_uav30.py to generate updated Table 5, then update main.tex.')
else:
    import datetime
    now = datetime.datetime.now()
    est_done = now + datetime.timedelta(minutes=eta_min)
    print(f'Estimated completion: {est_done.strftime("%H:%M")} (now is {now.strftime("%H:%M")})')