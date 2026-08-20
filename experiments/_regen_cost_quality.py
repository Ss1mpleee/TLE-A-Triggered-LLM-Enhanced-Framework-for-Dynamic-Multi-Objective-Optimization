"""Regenerate fig_cost_quality using overall_median (consistent with paper §5.5 18.88/44.18 claim)."""
import json
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib as mpl

# Replicate constants from plot_tevc.py
ALGOS = ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A', 'MOEA/DD', 'TLE']
COLORS = {
    'DE': '#9aa3a8',
    'DE-LM-static-trigger': '#7eb6d9',
    'PPS-DMOEA': '#d49bc4',
    'DNSGA-II-A': '#4ca28a',
    'MOEA/DD': '#e6b94d',
    'TLE': '#e8763a',
}
LABELS = {
    'DE': 'DE (no LLM)',
    'DE-LM-static-trigger': 'DE-LM-static (heuristic)',
    'PPS-DMOEA': 'PPS-DMOEA',
    'DNSGA-II-A': 'DNSGA-II-A',
    'MOEA/DD': 'MOEA/DD',
    'TLE': 'TLE (UCB1 bandit)',
}

# Load data
with open(r'results\raw\sec_main_v3.json', encoding='utf-8') as f:
    main = json.load(f)

by_a = defaultdict(lambda: {'inv': [], 'igd': []})
for r in main:
    if 'invocations' in r and r.get('igd') is not None:
        by_a[r['algo']]['inv'].append(r['invocations'])
        by_a[r['algo']]['igd'].append(r['igd'])

mpl.rcParams.update({
    'font.family': 'DejaVu Serif',
    'font.size': 10,
    'savefig.dpi': 300,
})

fig, ax = plt.subplots(figsize=(8.5, 5.8), constrained_layout=True)

ZERO_INV_JITTER = {'DE': 0.0, 'PPS-DMOEA': 1.2, 'DNSGA-II-A': 2.4, 'MOEA/DD': 0.6}
plotted = []
for algo in ALGOS:
    d = by_a[algo]
    if d['inv']:
        inv_mean = np.mean(d['inv'])
        igds_filt = [g for g in d['igd'] if g < 1e3]
        y = np.median(igds_filt) if igds_filt else 0  # overall median
        if inv_mean == 0:
            x = ZERO_INV_JITTER.get(algo, 0)
            xerr = 0
        else:
            x = inv_mean
            xerr = np.std(d['inv'])
        igd_arr = np.array(igds_filt)
        yerr_lo = max(0.0, y - np.percentile(igd_arr, 25))
        yerr_hi = max(0.0, np.percentile(igd_arr, 75) - y)
        ax.errorbar(x, y, xerr=xerr, yerr=[[yerr_lo], [yerr_hi]],
                    fmt='o', color=COLORS[algo], markersize=11,
                    markeredgecolor='black', markeredgewidth=0.8,
                    ecolor=COLORS[algo], elinewidth=1.2, capsize=3,
                    label=LABELS[algo], alpha=0.95, zorder=3)
        plotted.append((algo, x, y))

# Label placement
left_cluster = sorted([p for p in plotted if p[1] < 5], key=lambda p: p[2])
label_pos = {}
for i, (algo, x, y) in enumerate(left_cluster):
    label_pos[algo] = (-1.5, 0.55 + 0.08 * i, 'left')
for algo, x, y in plotted:
    if algo in label_pos:
        tx, ty, ha = label_pos[algo]
        ax.annotate(algo, xy=(x, y), xytext=(tx, ty),
                    textcoords='data', fontsize=9, fontweight='bold',
                    color=COLORS[algo], ha=ha,
                    arrowprops=dict(arrowstyle='-', color='gray',
                                    lw=0.5, alpha=0.5))
    else:
        ax.annotate(algo, xy=(x, y), xytext=(10, 6),
                    textcoords='offset points', fontsize=9,
                    fontweight='bold', color=COLORS[algo])

# Iso-cost-norm hyperbolas (median-based, matching paper §5.5)
# TLE: 18.88 IGD/1000 calls, DE-LM-static: 44.18 IGD/1000 calls
xx = np.linspace(2, 60, 100)
yy_tle = 18.88 * xx / 1000
yy_dels = 44.18 * xx / 1000
ax.plot(xx, yy_tle, '--', color=COLORS['TLE'], lw=1.2, alpha=0.7,
        label='TLE iso-cost-norm (18.88 IGD/1000 calls)')
ax.plot(xx, yy_dels, '--', color=COLORS['DE-LM-static-trigger'], lw=1.2, alpha=0.7,
        label='DE-LM-static iso-cost-norm (44.18 IGD/1000 calls)')

ax.set_xlabel('Avg LLM invocations per run (cost, lower is better)')
ax.set_ylabel('Overall median IGD across 14 problems × $n=30$ seeds = 420 IGDs\n(quality, lower is better, log scale)')
ax.set_yscale('log')
ax.set_title('Cost vs. quality tradeoff on the 14 CEC 2018 benchmarks (n=30 seeds per problem)\n'
             'left cluster: 4 zero-LLM-cost algos (x-jittered for readability); 2.34× better cost-norm for TLE')
ax.grid(alpha=0.3, which='both')
ax.legend(loc='upper right', framealpha=0.95, edgecolor='lightgray',
          fontsize=8)
ax.set_xlim(left=-3, right=58)
ax.set_ylim(bottom=0.3, top=2.0)

# Output
import os
out_dir = r'D:\新论文\论文\_submission'
plt.savefig(os.path.join(out_dir, 'fig_cost_quality.png'), bbox_inches='tight')
plt.savefig(os.path.join(out_dir, 'fig_cost_quality.pdf'), bbox_inches='tight')
print(f'Saved fig_cost_quality.png and .pdf')
print('  per-algo (x, y):')
for algo, x, y in plotted:
    print(f'    {algo:24s} x={x:.2f} y={y:.4f}')
