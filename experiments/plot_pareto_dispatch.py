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

"""S5: Pareto fronts for DF1, DF5, DF7 across DE, DNSGA-II-A, TLE.

Main paper already shows DF2 (catastrophic failure). SM shows DF1/DF5/DF7
which all reach reasonable convergence, making them useful for "what does
TLE actually produce" comparison.

Output: figures/fig_pareto_dispatch.png (and .pdf)
"""
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

SRC = RAW_DIR / "exp_pareto_fronts.json"
OUT_PNG = FIG_DIR / "fig_pareto_dispatch.png"
OUT_PDF = FIG_DIR / "fig_pareto_dispatch.pdf"

ALGOS = ['DE', 'DNSGA-II-A', 'TLE']
ALGO_LABELS = {'DE': 'DE', 'DNSGA-II-A': 'DNSGA-II-A', 'TLE': 'TLE'}
COLORS = {'DE': '#9aa3a8', 'DNSGA-II-A': '#4ca28a', 'TLE': '#e8763a'}
MARKERS = {'DE': 'o', 'DNSGA-II-A': 's', 'TLE': '^'}
PROBLEMS = ['DF1', 'DF5', 'DF7']


def main():
    data = json.load(open(SRC, encoding='utf-8'))

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

    fig, axes = plt.subplots(1, 3, figsize=(8.5, 3.0))
    fig.suptitle(
        'Pareto fronts after 200 generations (best of 3 seeds)',
        fontsize=11, y=1.00,
    )

    for ax, prob in zip(axes, PROBLEMS):
        for algo in ALGOS:
            # collect all nd fronts across seeds, take non-dominated union
            all_pts = []
            for r in data:
                if r['algo'] == algo and r['problem'] == prob:
                    nd = np.array(r['pareto_front'])
                    all_pts.append(nd)
            if not all_pts:
                continue
            all_pts = np.vstack(all_pts)
            # plot
            ax.scatter(
                all_pts[:, 0], all_pts[:, 1],
                s=18, alpha=0.45, color=COLORS[algo],
                marker=MARKERS[algo], edgecolors='none',
                label=ALGO_LABELS[algo],
            )
        ax.set_title(f'({prob})', loc='left', fontsize=10)
        ax.set_xlabel('$f_1$')
        if prob == 'DF1':
            ax.set_ylabel('$f_2$')
        ax.grid(True, ls=':', alpha=0.4)

    # shared legend at bottom
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=3,
               bbox_to_anchor=(0.5, -0.02), frameon=False)

    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
    fig.savefig(OUT_PNG, bbox_inches='tight')
    fig.savefig(OUT_PDF, bbox_inches='tight')
    print(f'Saved {OUT_PNG}')


if __name__ == '__main__':
    main()