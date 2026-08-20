#!/usr/bin/env python
"""Check fig_budget_comparison data source."""
import json
import statistics
from collections import defaultdict
from pathlib import Path

RAW = Path(r'D:\新论文\实验\results\raw')

print("=" * 70)
print("sec_main_v3.json: DE/DE-LM-static/TLE on DF1/DF5 (the 3 budget variants)")
print("=" * 70)
data = json.load(open(RAW / 'sec_main_v3.json', encoding='utf-8'))
for algo in ['DE', 'DE-LM-static-trigger', 'TLE']:
    for prob in ['DF1', 'DF5']:
        rows = [r for r in data if r['algo'] == algo and r['problem'] == prob]
        igds = [r['igd'] for r in rows if r.get('igd') is not None]
        invs = [r.get('invocations', 0) or 0 for r in rows]
        if igds:
            print(f"  {algo:25s}  {prob}  n={len(igds):3d}  "
                  f"median_igd={statistics.median(igds):.4f}  "
                  f"mean_inv={statistics.mean(invs):.2f}")
print()
print("If the figure shows:")
print("  V0=DE on DF1=0.379, V1=DE-LM-static on DF1=0.643, V2=TLE on DF1=0.690")
print("  V0=DE on DF5=0.119, V1=DE-LM-static on DF5=0.174, V2=TLE on DF5=0.168")
print("Then the figure values match n=30 medians from sec_main_v3.json")
print()
print("BUT the LaTeX caption says 'V1 wins by 19.3% on DF5'")
print("  Actually: V1=0.174 (heuristic) is WORSE than V2=0.168 (UCB1) on DF5")
print("  Difference: (0.174-0.168)/0.168 = 3.6%, NOT 19.3%")
print()
print("Where does 19.3% come from? Let me check 5.5.2 text...")
