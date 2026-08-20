#!/usr/bin/env python
"""Per-problem invocations for the 3 budget variants."""
import json
import statistics
from pathlib import Path

RAW = Path(r'D:\新论文\实验\results\raw\sec_main_v3.json')
data = json.load(open(RAW, encoding='utf-8'))

print("Per-problem mean invocations (n=30) — should match fig_budget_comparison:")
for algo, label in [('DE', 'V0 (no LLM)'),
                     ('DE-LM-static-trigger', 'V1 (heuristic)'),
                     ('TLE', 'V2 (UCB1 bandit)')]:
    for prob in ['DF1', 'DF5']:
        rows = [r for r in data if r['algo'] == algo and r['problem'] == prob]
        invs = [r.get('invocations', 0) or 0 for r in rows]
        igd_mean = statistics.mean([r['igd'] for r in rows
                                     if r.get('igd') is not None and r['igd'] < 1e6])
        print(f"  {label:20s}  {prob}  mean_inv={statistics.mean(invs):.2f}  "
              f"mean_igd={igd_mean:.4f}")

print()
print("Figure shows:")
print("  DF1: V0=0 calls, V1=26 calls, V2=49 calls")
print("  DF5: V0=0 calls, V1=20 calls, V2=50 calls")
