#!/usr/bin/env python
"""Compute exact DE/DE-LM-static/TLE IGDs on DF1/DF5 from n=30 data
to verify if fig_budget_comparison.png can be regenerated cleanly.
"""
import json
import statistics
from pathlib import Path

RAW = Path(r'D:\新论文\实验\results\raw\sec_main_v3.json')
data = json.load(open(RAW, encoding='utf-8'))

print("=" * 72)
print("n=30 data for fig_budget_comparison (DE=no LLM, DE-LM-static=heuristic, TLE=UCB1)")
print("=" * 72)
mapping = {
    'DE':                   'V0 (no LLM, pure DE)',
    'DE-LM-static-trigger': 'V1 (heuristic decay)',
    'TLE':                  'V2 (UCB1 bandit)',
}
for algo, label in mapping.items():
    for prob in ['DF1', 'DF5']:
        rows = [r for r in data if r['algo'] == algo and r['problem'] == prob]
        igds = sorted([r['igd'] for r in rows if r.get('igd') is not None and r['igd'] < 1e6])
        invs = [r.get('invocations', 0) or 0 for r in rows]
        n = len(igds)
        if igds:
            med = statistics.median(igds)
            mean = statistics.mean(igds)
            std = statistics.stdev(igds) if len(igds) > 1 else 0
            mean_inv = statistics.mean(invs)
            print(f"  {label:30s}  {prob}  n={n}  "
                  f"median={med:.4f}  mean={mean:.4f}  std={std:.4f}  "
                  f"mean_inv={mean_inv:.2f}")

print()
print("Figure currently shows:")
print("  V0=0.379, V1=0.643, V2=0.690 (DF1)")
print("  V0=0.119, V1=0.174, V2=0.168 (DF5)")
print()
print("Hypothesis: figure values are MEAN (with outliers trimmed at 1e6)")
print("or MEDIAN with a slight rounding")
