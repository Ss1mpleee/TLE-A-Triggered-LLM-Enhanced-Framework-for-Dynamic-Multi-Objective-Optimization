#!/usr/bin/env python
"""
TLE-DMO reproduction script.

The four lines below make this script runnable from any working directory:
it puts the repository root on `sys.path` and exposes the standard result
directories as module-level `Path` constants.  Do not delete them.
"""
from __future__ import annotations
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

RAW_DIR   = REPO_ROOT / "results" / "raw"
FIG_DIR   = REPO_ROOT / "results" / "figures"
CACHE_DIR = REPO_ROOT / "results" / "llm_cache"

"""S1: Per-seed IGD distribution box plots.

Replaces fig_main_igd.png which duplicated Table 1. Box plots show distribution
shape (skew, outliers, variance pattern) that mean+/-std hides.

Output: figures/fig_seed_boxplots.png (and .pdf)
"""
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

SRC = RAW_DIR / "sec_main_v3.json"
OUT_PNG = FIG_DIR / "fig_seed_boxplots.png"
OUT_PDF = FIG_DIR / "fig_seed_boxplots.pdf"

ALGOS = ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A', 'MOEA/DD', 'TLE']
ALGO_LABELS = {
    'DE': 'DE',
    'DE-LM-static-trigger': 'DE-LM-static',
    'PPS-DMOEA': 'PPS-DMOEA',
    'DNSGA-II-A': 'DNSGA-II-A',
    'MOEA/DD': 'MOEA/DD',
    'TLE': 'TLE',
}
COLORS = {
    'DE': '#9aa3a8',
    'DE-LM-static-trigger': '#7eb6d9',
    'PPS-DMOEA': '#d49bc4',
    'DNSGA-II-A': '#4ca28a',
    'MOEA/DD': '#e6b94d',
    'TLE': '#e8763a',
}
PROBLEMS = ['DF1', 'DF2', 'DF5', 'DF7']  # exclude DF3 to keep layout clean


def main():
    data = json.load(open(SRC, encoding='utf-8'))
    rows = [r for r in data if r['problem'] in PROBLEMS and r['algo'] in ALGOS]
    # Build per-(problem, algo) list of IGD values
    grouped = {(p, a): [] for p in PROBLEMS for a in ALGOS}
    for r in rows:
        grouped[(r['problem'], r['algo'])].append(r['igd'])

    # Clip DF2 outliers for readability (log scale)
    for a in ALGOS:
        vals = grouped[('DF2', a)]
        if vals:
            cap = np.percentile(vals, 75) + 1.5 * (np.percentile(vals, 75) - np.percentile(vals, 25))
            cap = max(cap, 10.0)
            grouped[('DF2', a)] = [min(v, cap) for v in vals]

    mpl.rcParams.update({
        'font.family': 'DejaVu Serif',
        'font.size': 9,
        'axes.titlesize': 10,
        'axes.labelsize': 9.5,
        'xtick.labelsize': 8.5,
        'ytick.labelsize': 8.5,
        'legend.fontsize': 8,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'savefig.dpi': 300,
    })

    fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.4))
    fig.suptitle(
        r'Per-seed IGD distribution (8 seeds $\times$ 6 algorithms $\times$ 4 problems)',
        fontsize=11, y=0.995,
    )

    for ax, prob in zip(axes.flat, PROBLEMS):
        # collect boxplot data
        bp_data = [grouped[(prob, a)] for a in ALGOS]
        bp = ax.boxplot(
            bp_data, positions=range(len(ALGOS)), widths=0.6,
            patch_artist=True, showmeans=True, meanline=False,
            medianprops=dict(color='black', lw=1.2),
            meanprops=dict(marker='D', markerfacecolor='white',
                           markeredgecolor='black', markersize=4),
            flierprops=dict(marker='o', ms=3, mfc='gray', mec='gray', alpha=0.6),
            whiskerprops=dict(color='gray', lw=0.8),
            capprops=dict(color='gray', lw=0.8),
        )
        for patch, algo in zip(bp['boxes'], ALGOS):
            patch.set_facecolor(COLORS[algo])
            patch.set_alpha(0.75)
            patch.set_edgecolor('black')
            patch.set_linewidth(0.6)

        # log scale for DF2 to handle MOEA/DD outlier
        if prob == 'DF2':
            ax.set_yscale('symlog', linthresh=0.5)
            ax.set_ylim(-0.5, 200)
        else:
            ax.set_yscale('log')

        ax.set_xticks(range(len(ALGOS)))
        ax.set_xticklabels([ALGO_LABELS[a] for a in ALGOS], rotation=20, ha='right')
        ax.set_title(f'({prob})', loc='left', fontsize=10)
        ax.set_ylabel('IGD (lower = better)')
        ax.grid(True, axis='y', ls=':', alpha=0.4)

    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUT_PNG, bbox_inches='tight')
    fig.savefig(OUT_PDF, bbox_inches='tight')
    print(f'Saved {OUT_PNG}')


if __name__ == '__main__':
    main()