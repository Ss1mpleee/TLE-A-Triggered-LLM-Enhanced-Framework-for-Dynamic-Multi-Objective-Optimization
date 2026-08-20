#!/usr/bin/env python
"""Regenerate fig_budget_comparison.png with n=30 data from sec_main_v3.json.

v2: fix layout — auto ylim per panel, bar height matches data range.
"""
from __future__ import annotations
from pathlib import Path
import json
import statistics
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(r'D:\新论文\实验')
RAW = REPO_ROOT / 'results' / 'raw' / 'sec_main_v3.json'
SUB = REPO_ROOT.parent / '论文' / '_submission'

data = json.load(open(RAW, encoding='utf-8'))

VARIANTS = [
    ('DE',                   'V$0$: pure DE',     '#9aa3a8'),
    ('DE-LM-static-trigger', 'V$1$: heuristic',   '#e6a23a'),
    ('TLE',                  'V$2$: UCB1 (TLE)',  '#e8763a'),
]
PROBLEMS = ['DF1', 'DF5']

results = {}
for algo, _, _ in VARIANTS:
    for prob in PROBLEMS:
        rows = [r for r in data if r['algo'] == algo and r['problem'] == prob]
        igds = [r['igd'] for r in rows
                if r.get('igd') is not None and r['igd'] < 1e6]
        invs = [r.get('invocations', 0) or 0 for r in rows]
        if igds:
            results[(algo, prob)] = {
                'mean_igd': statistics.mean(igds),
                'std_igd': statistics.stdev(igds) if len(igds) > 1 else 0.0,
                'mean_inv': statistics.mean(invs),
            }

fig, axes = plt.subplots(1, 2, figsize=(8.0, 4.0))
for ax, prob in zip(axes, PROBLEMS):
    means = []
    stds = []
    invs = []
    colors = []
    labels = []
    for algo, label, color in VARIANTS:
        d = results.get((algo, prob))
        if d is None:
            continue
        means.append(d['mean_igd'])
        stds.append(d['std_igd'])
        invs.append(d['mean_inv'])
        colors.append(color)
        labels.append(label)
    x = np.arange(len(means))
    bars = ax.bar(x, means, yerr=stds, color=colors, alpha=0.92,
                  edgecolor='black', linewidth=0.5, capsize=5,
                  error_kw={'lw': 0.8}, width=0.65)
    for i, (m, s) in enumerate(zip(means, stds)):
        # IGD value above error bar
        ax.text(i, m + s + max(stds) * 0.05, f'{m:.3f}',
                ha='center', fontsize=10, fontweight='bold')
    for i, inv in enumerate(invs):
        # invocation count INSIDE bar (white text)
        ax.text(i, max(means) * 0.04, f'({inv:.0f} calls)',
                ha='center', va='bottom', fontsize=8.5,
                color='white', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_xlabel('budget scheduler variant', fontsize=9.5)
    ax.set_title(f'({prob})', fontsize=11, loc='left', pad=4)
    ax.grid(axis='y', alpha=0.3)
    # Auto ylim: 0 → max + headroom
    ymax = max(m + s for m, s in zip(means, stds)) * 1.30
    ax.set_ylim(bottom=0, top=ymax)

axes[0].set_ylabel('Final IGD (lower is better, mean $\\pm$ std)',
                   fontsize=10)
fig.suptitle('Budget-scheduler ablation on DF1 and DF5 '
             '($n = 30$ seeds; outliers $>10^{6}$ trimmed)',
             fontsize=10.5, y=1.00)
fig.tight_layout()
out_png = SUB / 'fig_budget_comparison.png'
fig.savefig(out_png, dpi=300, bbox_inches='tight')
fig.savefig(out_png.with_suffix('.pdf'), bbox_inches='tight')
print(f"Saved {out_png}")
