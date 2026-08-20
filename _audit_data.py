#!/usr/bin/env python
"""Audit data files for figure-data consistency."""
import json
import statistics
from collections import defaultdict
from pathlib import Path

RAW = Path(r'D:\新论文\实验\results\raw')

print("=" * 70)
print("1) sec_main_v3.json (6-algorithm main, 14 probs x 30 seeds)")
print("=" * 70)
data = json.load(open(RAW / 'sec_main_v3.json', encoding='utf-8'))
print(f"  Total rows: {len(data)}")
print(f"  Fields: {list(data[0].keys())}")
by_algo = defaultdict(list)
for r in data:
    if 'igd' in r and r['igd'] is not None:
        by_algo[r['algo']].append(r)
for algo in sorted(by_algo):
    igds = [r['igd'] for r in by_algo[algo]]
    invs = [r.get('invocations', 0) or 0 for r in by_algo[algo]]
    print(f"  {algo:25s}  n={len(igds):4d}  "
          f"mean_igd={statistics.mean(igds):.4f}  "
          f"median_igd={statistics.median(igds):.4f}  "
          f"mean_inv={statistics.mean(invs):.2f}")

print()
print("=" * 70)
print("2) exp7_ablation_combined.json (T0/T1/T2/T3 ablation, 14 x 30)")
print("=" * 70)
data = json.load(open(RAW / 'exp7_ablation_combined.json', encoding='utf-8'))
print(f"  Total rows: {len(data)}")
print(f"  Fields: {list(data[0].keys())}")
by_ver = defaultdict(list)
for r in data:
    by_ver[r['version']].append(r)
for ver in sorted(by_ver):
    igds = [r['igd'] for r in by_ver[ver] if r.get('igd') is not None]
    invs = [r.get('invocations', 0) or 0 for r in by_ver[ver]]
    print(f"  {ver:15s}  n={len(igds):4d}  "
          f"mean_igd={statistics.mean(igds):.4f}  "
          f"median_igd={statistics.median(igds):.4f}  "
          f"mean_inv={statistics.mean(invs):.2f}")
print()
print("  --- T3 (V3_triple) invocations per problem (sorted DF#) ---")
t3 = [r for r in data if r['version'] == 'V3_triple']
by_prob = defaultdict(list)
for r in t3:
    by_prob[r['problem']].append(r.get('invocations', 0) or 0)
for prob in sorted(by_prob, key=lambda x: int(x.replace('DF',''))):
    invs = by_prob[prob]
    print(f"  {prob:6s}  n={len(invs):3d}  mean_inv={statistics.mean(invs):.2f}  "
          f"min={min(invs)}  max={max(invs)}  "
          f"pct_of_200={statistics.mean(invs)/200*100:.1f}%")

print()
print("=" * 70)
print("3) exp6_cross_llm_n14.json (3 LLMs x 14 probs x 30 seeds)")
print("=" * 70)
data = json.load(open(RAW / 'exp6_cross_llm_n14.json', encoding='utf-8'))
print(f"  Total rows: {len(data)}")
print(f"  Fields: {list(data[0].keys())}")
by_llm_prob = defaultdict(list)
for r in data:
    by_llm_prob[(r['model'], r['prob'])].append(r)
print("  Per-(LLM, problem) mean IGD and invocations:")
for key in sorted(by_llm_prob.keys()):
    rows = by_llm_prob[key]
    igds = [r['igd'] for r in rows if r.get('igd') is not None]
    invs = [r.get('invocations', 0) or 0 for r in rows]
    if igds:
        print(f"  {str(key):60s}  n={len(igds):3d}  "
              f"mean_igd={statistics.mean(igds):.4f}  "
              f"mean_inv={statistics.mean(invs):.2f}")
