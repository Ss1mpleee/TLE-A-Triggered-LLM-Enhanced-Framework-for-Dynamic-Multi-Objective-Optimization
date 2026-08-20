#!/usr/bin/env python
"""Check the actual data for DF9/DF10/DF11/DF14 and the small dots."""
import json
import statistics
from collections import defaultdict
from pathlib import Path

RAW = Path(r'D:\新论文\实验\results\raw\exp7_ablation_combined.json')
data = json.load(open(RAW, encoding='utf-8'))

print("=" * 72)
print("DF9/DF10/DF11/DF14 IGD statistics per version (n=30 each)")
print("=" * 72)
for prob in ['DF9', 'DF10', 'DF11', 'DF14']:
    print(f"\n--- {prob} ---")
    for ver in ['V0_baseline', 'V1_single', 'V2_double', 'V3_triple']:
        rows = [r for r in data if r['problem'] == prob and r['version'] == ver]
        igds = [r['igd'] for r in rows if r.get('igd') is not None]
        if igds:
            mn = min(igds)
            mx = max(igds)
            med = statistics.median(igds)
            std = statistics.stdev(igds) if len(igds) > 1 else 0
            unique_count = len(set(igds))
            print(f"  {ver:15s}  n={len(igds):3d}  min={mn:.4f}  "
                  f"max={mx:.4f}  median={med:.4f}  std={std:.4f}  unique={unique_count}")

print()
print("=" * 72)
print("DF2 outliers (the 'small dots' near the top, clipped at 2.0)")
print("=" * 72)
for ver in ['V0_baseline', 'V1_single', 'V2_double', 'V3_triple']:
    rows = [r for r in data if r['problem'] == 'DF2' and r['version'] == ver]
    igds = [r['igd'] for r in rows if r.get('igd') is not None]
    if igds:
        sorted_igds = sorted(igds)
        # IQR
        q1 = sorted_igds[len(sorted_igds)//4]
        q3 = sorted_igds[3*len(sorted_igds)//4]
        iqr = q3 - q1
        upper_fence = q3 + 1.5 * iqr
        outliers = [g for g in igds if g > upper_fence]
        print(f"  {ver:15s}  Q1={q1:.4f}  Q3={q3:.4f}  IQR={iqr:.4f}  "
              f"upper_fence={upper_fence:.4f}  outliers_above_fence={len(outliers)}")
        if outliers:
            for o in sorted(outliers)[:3]:
                print(f"      outlier: {o:.2f}")

print()
print("=" * 72)
print("DF11 outliers (the dots near 1.4-1.6 in the figure)")
print("=" * 72)
for ver in ['V0_baseline', 'V1_single', 'V2_double', 'V3_triple']:
    rows = [r for r in data if r['problem'] == 'DF11' and r['version'] == ver]
    igds = [r['igd'] for r in rows if r.get('igd') is not None]
    if igds:
        sorted_igds = sorted(igds)
        q1 = sorted_igds[len(sorted_igds)//4]
        q3 = sorted_igds[3*len(sorted_igds)//4]
        iqr = q3 - q1
        upper_fence = q3 + 1.5 * iqr
        outliers = [g for g in igds if g > upper_fence]
        print(f"  {ver:15s}  Q1={q1:.4f}  Q3={q3:.4f}  IQR={iqr:.4f}  "
              f"upper_fence={upper_fence:.4f}  outliers_above_fence={len(outliers)}")
        if outliers:
            for o in sorted(outliers)[:3]:
                print(f"      outlier: {o:.2f}")
