#!/usr/bin/env python
"""
TLE-DMO Nemenyi CD diagram (6-algorithm comparison).

Uses the standard Demsar 2006 layout — single horizontal axis with
markers on it, integer ticks 1..k below, CD bar on top, clique bars
just above the axis, short labels with leader lines, and a bottom
legend mapping short labels to full names.

Source data: results/raw/sec_main_v3.json (6 algos x 14 problems x 30 seeds).
"""
from __future__ import annotations
from pathlib import Path
import json
import math
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

RAW_DIR   = REPO_ROOT / "results" / "raw"
FIG_DIR   = REPO_ROOT / "results" / "figures"
SUB_DIR   = REPO_ROOT.parent / "论文" / "_submission"
FIG_DIR.mkdir(parents=True, exist_ok=True)
SUB_DIR.mkdir(parents=True, exist_ok=True)

OUT_PNG = FIG_DIR / "fig_nemenyi_cd.png"
OUT_PDF = FIG_DIR / "fig_nemenyi_cd.pdf"

ALGOS = ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A', 'MOEA/DD', 'TLE']
ALGO_LABELS = {
    'DE': 'DE (no LLM)',
    'DE-LM-static-trigger': 'DE-LM-static (heuristic)',
    'PPS-DMOEA': 'PPS-DMOEA',
    'DNSGA-II-A': 'DNSGA-II-A',
    'MOEA/DD': 'MOEA/DD',
    'TLE': 'TLE (UCB1 bandit)',
}
COLORS = {
    'DE': '#9aa3a8',
    'DE-LM-static-trigger': '#7eb6d9',
    'PPS-DMOEA': '#d49bc4',
    'DNSGA-II-A': '#4ca28a',
    'MOEA/DD': '#e6b94d',
    'TLE': '#e8763a',
}
SHORT = {
    'DE': 'DE',
    'DE-LM-static-trigger': 'DE-LM',
    'PPS-DMOEA': 'PPS',
    'DNSGA-II-A': 'DNSGA',
    'MOEA/DD': 'MOEA/DD',
    'TLE': 'TLE',
}


def main():
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib as mpl

    data = json.load(open(RAW_DIR / "sec_main_v3.json", encoding='utf-8'))
    problems = sorted({r['problem'] for r in data})
    k = len(ALGOS)
    N = len(problems)

    # Mean IGD per (algo, prob).  MOEA/DD on DF2 is imputed (its raw
    # values are catastrophic at 1e7-1e27, so they would dominate the
    # average if unfiltered).
    algo_ranks = {a: [] for a in ALGOS}
    for prob in problems:
        means = {}
        for a in ALGOS:
            if a == 'MOEA/DD' and prob == 'DF2':
                means[a] = float('inf')  # sentinel
                continue
            vals = [r['igd'] for r in data
                    if r['problem'] == prob and r['algo'] == a]
            means[a] = float(np.mean(vals)) if vals else float('inf')
        sorted_algos = sorted(means, key=means.get)
        for rank, a in enumerate(sorted_algos, start=1):
            if a == 'MOEA/DD' and prob == 'DF2':
                continue
            algo_ranks[a].append(rank)
    moeadd_ranks_other = algo_ranks['MOEA/DD']
    algo_ranks['MOEA/DD'].append(float(np.mean(moeadd_ranks_other)))

    avg_ranks = {a: float(np.mean(algo_ranks[a])) for a in ALGOS}

    # Nemenyi critical difference (alpha=0.05, k=6 -> q=2.850, Demšar 2006 Table 5b)
    q = 2.850
    cd = q * math.sqrt(k * (k + 1) / (6 * N))

    sorted_algos = sorted(ALGOS, key=lambda a: avg_ranks[a])
    ranks = [avg_ranks[a] for a in sorted_algos]
    colors = [COLORS[a] for a in sorted_algos]
    shorts = [SHORT[a] for a in sorted_algos]

    mpl.rcParams.update({
        'font.family': 'DejaVu Serif',
        'font.size': 10,
        'savefig.dpi': 300,
    })
    fig, ax = plt.subplots(figsize=(9.0, 3.2))

    # Standard Demšar 2006 layout
    ax.set_xlim(0.5, k + 0.5)
    ax.set_ylim(-1.6, 1.45)
    ax.set_yticks([])

    # Single axis line + integer tick labels
    ax.plot([0.5, k + 0.5], [0.0, 0.0], color='black', lw=0.9, zorder=2)
    for x in range(1, k + 1):
        ax.plot([x, x], [0.0, -0.05], color='black', lw=0.9, zorder=2)
    ax.set_xticks(range(1, k + 1))
    ax.set_xticklabels([str(x) for x in range(1, k + 1)], fontsize=10)
    ax.tick_params(axis='x', length=0, pad=4)

    # CD reference bar on top
    cd_y = 1.20
    ax.plot([1, 1 + cd], [cd_y, cd_y], color='black', lw=1.5, zorder=3)
    ax.plot([1, 1], [cd_y - 0.07, cd_y + 0.07], color='black', lw=1.5, zorder=3)
    ax.plot([1 + cd, 1 + cd], [cd_y - 0.07, cd_y + 0.07], color='black', lw=1.5, zorder=3)
    ax.text(1 + cd / 2, cd_y + 0.12, f'CD = {cd:.2f}',
            ha='center', va='bottom', fontsize=10.5, fontweight='bold')

    # Markers ON the axis (y=0)
    for algo, rank, color in zip(sorted_algos, ranks, colors):
        ax.plot(rank, 0.0, 'o', ms=13, color=color, mec='black', mew=0.9, zorder=4)

    # Labels: vertical-stack with leader lines to avoid horizontal overlap
    sorted_by_rank = sorted(zip(sorted_algos, ranks, shorts, colors),
                            key=lambda kr: kr[1])
    label_y = {}  # algo -> y_offset
    y_levels = [-0.40, -0.75, -1.10, -1.45]
    for i, (algo, rank, short, color) in enumerate(sorted_by_rank):
        placed = False
        for y_off in y_levels:
            collide = False
            for prev_algo, (px, py) in label_y.items():
                if abs(rank - px) < 0.40 and abs(y_off - py) < 0.15:
                    collide = True
                    break
            if not collide:
                label_y[algo] = (rank, y_off)
                placed = True
                break
        if not placed:
            label_y[algo] = (rank, y_levels[0])

    for algo, rank, short, color in zip(sorted_algos, ranks, shorts, colors):
        y_off = label_y[algo][1]
        ax.plot([rank, rank], [-0.05, y_off + 0.05], color='gray', lw=0.6, zorder=2)
        ax.text(rank, y_off, short, ha='center', va='top',
                fontsize=11, fontweight='bold', color=color)

    # Bottom legend: short label -> full name
    legend_handles = [f"{SHORT[a]} = {ALGO_LABELS[a]}" for a in sorted_algos]
    legend_text = "    ".join(legend_handles)
    fig.text(0.5, -0.02, legend_text, ha='center', va='top',
             fontsize=8.5, style='italic')

    # Clique bars just above the axis (within CD of each other)
    cliques = []
    cur = [sorted_algos[0]]
    for a in sorted_algos[1:]:
        if abs(avg_ranks[a] - avg_ranks[cur[0]]) <= cd:
            cur.append(a)
        else:
            cliques.append(cur)
            cur = [a]
    cliques.append(cur)

    clique_y = 0.20
    for clique in cliques:
        if len(clique) > 1:
            x_min = min(avg_ranks[a] for a in clique) - 0.04
            x_max = max(avg_ranks[a] for a in clique) + 0.04
            ax.plot([x_min, x_max], [clique_y, clique_y],
                    color='#aa3322', lw=2.8, zorder=3)
            ax.plot([x_min, x_min], [clique_y - 0.04, clique_y + 0.04],
                    color='#aa3322', lw=2.8)
            ax.plot([x_max, x_max], [clique_y - 0.04, clique_y + 0.04],
                    color='#aa3322', lw=2.8)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.set_xlabel('Average Friedman rank (lower is better)', fontsize=10, labelpad=4)

    title = (f'Nemenyi CD diagram (Friedman $\\chi^2$ test, '
             f'$k$={k} algorithms, $N$={N} problems, '
             f'$n$={30} seeds per problem, $\\alpha$=0.05)')
    fig.suptitle(title, fontsize=10.5, y=1.02)
    fig.tight_layout()
    fig.savefig(OUT_PNG, bbox_inches='tight')
    fig.savefig(OUT_PDF, bbox_inches='tight')
    print(f'Saved {OUT_PNG}')
    print('Average ranks:')
    for a in sorted_algos:
        print(f'  {ALGO_LABELS[a]:28s}  rank={avg_ranks[a]:.2f}')
    print(f'CD = {cd:.3f}')

    # Copy to submission
    import shutil
    for ext in ('.png', '.pdf'):
        shutil.copy2(FIG_DIR / f'fig_nemenyi_cd{ext}',
                     SUB_DIR / f'fig_nemenyi_cd{ext}')


if __name__ == '__main__':
    main()
