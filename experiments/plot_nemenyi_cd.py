"""S2: Nemenyi critical-difference diagram.

Replaces nothing (new). Visualizes Friedman + Nemenyi post-hoc ranking.
6 algorithms ranked across 5 problems (8 seeds each). CD = q_alpha * sqrt(k(k+1)/6N).

Output: figures/fig_nemenyi_cd.png (and .pdf)
"""
import json
import math
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

SRC = Path(r'D:\新论文\实验\results\raw\sec_main_v3.json')
OUT_PNG = Path(r'D:\新论文\论文\figures\fig_nemenyi_cd.png')
OUT_PDF = Path(r'D:\新论文\论文\figures\fig_nemenyi_cd.pdf')

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


def main():
    data = json.load(open(SRC, encoding='utf-8'))
    problems = sorted({r['problem'] for r in data})
    k = len(ALGOS)
    N = len(problems)

    # Compute ranks per problem (lower IGD = better = rank 1)
    algo_ranks = {a: [] for a in ALGOS}
    for prob in problems:
        # mean IGD per algo
        means = {}
        for a in ALGOS:
            vals = [r['igd'] for r in data if r['problem'] == prob and r['algo'] == a]
            means[a] = float(np.mean(vals)) if vals else float('inf')
        # rank
        sorted_algos = sorted(means, key=means.get)
        for rank, a in enumerate(sorted_algos, start=1):
            algo_ranks[a].append(rank)

    avg_ranks = {a: float(np.mean(algo_ranks[a])) for a in ALGOS}

    # Critical difference (Nemenyi, alpha=0.05, k=6 -> q=2.850)
    q = 2.850
    cd = q * math.sqrt(k * (k + 1) / (6 * N))

    # Sort by rank ascending (best on left)
    sorted_algos = sorted(ALGOS, key=lambda a: avg_ranks[a])
    ranks = [avg_ranks[a] for a in sorted_algos]
    labels = [ALGO_LABELS[a] for a in sorted_algos]
    colors = [COLORS[a] for a in sorted_algos]

    # Detect label overlaps and assign vertical offsets
    label_y = {}
    overlap_threshold = 0.65  # conservative horizontal label width
    sorted_pairs = sorted(enumerate(sorted_algos), key=lambda p: ranks[p[0]])
    for i, (idx, a) in enumerate(sorted_pairs):
        r = ranks[idx]
        placed = False
        for y_off in [0.55, 0.80, 1.05]:
            collide = False
            for prev_a, (px, py) in label_y.items():
                if abs(r - px) < overlap_threshold and abs(y_off - py) < 0.15:
                    collide = True
                    break
            if not collide:
                label_y[a] = (r, y_off)
                placed = True
                break
        if not placed:
            label_y[a] = (r, 0.55)

    mpl.rcParams.update({
        'font.family': 'DejaVu Serif',
        'font.size': 10,
        'savefig.dpi': 300,
    })
    fig, ax = plt.subplots(figsize=(7.8, 3.0))

    # Horizontal axis: ranks
    ax.set_xlim(0.2, k + 0.8)
    ax.set_ylim(-0.7, 1.45)
    ax.set_xticks(range(1, k + 1))
    ax.set_yticks([])

    # Bottom axis line
    for x in range(1, k + 1):
        ax.plot([x, x], [0.0, 0.08], color='black', lw=0.8, zorder=2)
        ax.text(x, -0.12, str(x), ha='center', va='top', fontsize=9)

    # CD bar
    cd_y = 1.28
    ax.plot([1, cd + 1], [cd_y, cd_y], color='black', lw=1.3)
    ax.plot([1, 1], [cd_y - 0.06, cd_y + 0.06], color='black', lw=1.3)
    ax.plot([cd + 1, cd + 1], [cd_y - 0.06, cd_y + 0.06], color='black', lw=1.3)
    ax.text(1 + cd / 2, cd_y + 0.10, f'CD = {cd:.2f}', ha='center', va='bottom', fontsize=9.5)

    # Algorithm markers + labels
    for a, rank, label, color in zip(sorted_algos, ranks, labels, colors):
        _, y_off = label_y[a]
        ax.plot(rank, 0.20, 'o', ms=11, color=color, mec='black', mew=0.8, zorder=3)
        # connector line
        ax.plot([rank, rank], [0.20, y_off - 0.03], color='gray', lw=0.5, zorder=2)
        ax.text(rank, y_off, label, ha='center', va='bottom', fontsize=9.5,
                fontweight='bold')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.set_xlabel('Average Friedman rank (lower is better)', fontsize=10)

    # Cliques: groups that are not significantly different (within CD)
    cliques = []
    cur = [sorted_algos[0]]
    for a in sorted_algos[1:]:
        if abs(avg_ranks[a] - avg_ranks[cur[0]]) <= cd:
            cur.append(a)
        else:
            cliques.append(cur)
            cur = [a]
    cliques.append(cur)

    # Draw clique bars below the axis
    clique_y = -0.55
    for clique in cliques:
        if len(clique) > 1:
            x_min = min(avg_ranks[a] for a in clique) - 0.05
            x_max = max(avg_ranks[a] for a in clique) + 0.05
            ax.plot([x_min, x_max], [clique_y, clique_y], color='#aa3322', lw=2.5, zorder=3)
            ax.plot([x_min, x_min], [clique_y - 0.04, clique_y + 0.04], color='#aa3322', lw=2.5)
            ax.plot([x_max, x_max], [clique_y - 0.04, clique_y + 0.04], color='#aa3322', lw=2.5)

    fig.suptitle(
        f'Nemenyi CD diagram (Friedman $\\chi^2$ test, $k$={k} algorithms, $N$={N} problems, $\\alpha$=0.05)',
        fontsize=10.5, y=1.05,
    )
    fig.tight_layout()
    fig.savefig(OUT_PNG, bbox_inches='tight')
    fig.savefig(OUT_PDF, bbox_inches='tight')
    print(f'Saved {OUT_PNG}')
    print('Average ranks:')
    for a in sorted_algos:
        print(f'  {ALGO_LABELS[a]:15s}  rank={avg_ranks[a]:.2f}')
    print(f'CD = {cd:.3f}')


if __name__ == '__main__':
    main()