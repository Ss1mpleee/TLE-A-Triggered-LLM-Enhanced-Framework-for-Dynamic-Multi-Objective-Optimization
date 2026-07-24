"""S4: Trigger entropy_threshold sensitivity plot.

Sweeps the entropy_threshold parameter (0.001 to 0.5) which controls when
the triple-signal trigger fires. Lower threshold = trigger more sensitive
= more LLM invocations.

Output: figures/fig_trigger_sweep.png (and .pdf)
"""
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

SRC = Path(r'D:\新论文\实验\results\raw\exp_trigger_threshold.json')
OUT_PNG = Path(r'D:\新论文\论文\figures\fig_trigger_sweep.png')
OUT_PDF = Path(r'D:\新论文\论文\figures\fig_trigger_sweep.pdf')

PROBLEMS = ['DF1', 'DF5']
PROBLEM_COLORS = {'DF1': '#7eb6d9', 'DF5': '#4ca28a'}


def main():
    data = json.load(open(SRC, encoding='utf-8'))
    # Group by (problem, tau)
    grouped = {}
    for r in data:
        key = (r['problem'], r['entropy_threshold'])
        grouped.setdefault(key, []).append((r['invocations'], r['igd']))

    mpl.rcParams.update({
        'font.family': 'DejaVu Serif',
        'font.size': 9,
        'axes.titlesize': 10,
        'axes.labelsize': 9.5,
        'xtick.labelsize': 8.5,
        'ytick.labelsize': 8.5,
        'legend.fontsize': 8.5,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'savefig.dpi': 300,
    })

    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.2))
    fig.suptitle(
        r'Trigger sensitivity: entropy threshold $\tau_e$ (lower = more sensitive = more LLM invocations)',
        fontsize=10.5, y=1.02,
    )

    for ax, prob in zip(axes, PROBLEMS):
        taus = sorted({r['entropy_threshold'] for r in data if r['problem'] == prob})
        invs_mean = [np.mean([x[0] for x in grouped[(prob, t)]]) for t in taus]
        invs_std = [np.std([x[0] for x in grouped[(prob, t)]]) for t in taus]
        igd_mean = [np.mean([x[1] for x in grouped[(prob, t)]]) for t in taus]
        igd_std = [np.std([x[1] for x in grouped[(prob, t)]]) for t in taus]

        color = PROBLEM_COLORS[prob]
        # Plot IGD vs tau
        ax.errorbar(taus, igd_mean, yerr=igd_std, fmt='o-', color=color,
                    lw=1.5, ms=7, capsize=3, label='IGD', zorder=3)
        ax.set_xscale('log')
        ax.set_xlabel(r'$\tau_e$ (entropy threshold, log scale)')
        ax.set_ylabel('IGD (lower = better)', color=color)
        ax.tick_params(axis='y', labelcolor=color)
        ax.grid(True, ls=':', alpha=0.4)

        # Inversions axis (right)
        ax2 = ax.twinx()
        ax2.errorbar(taus, invs_mean, yerr=invs_std, fmt='s--', color='#aa3322',
                     lw=1.2, ms=5, capsize=3, label='LLM invocations', zorder=2)
        ax2.set_ylabel('# LLM invocations', color='#aa3322')
        ax2.tick_params(axis='y', labelcolor='#aa3322')
        ax2.spines['top'].set_visible(False)

        # Mark default tau_e=0.05
        ax.axvline(0.05, ls=':', color='gray', alpha=0.6, lw=1.2)
        ylo, yhi = ax.get_ylim()
        ax.text(0.05, yhi - 0.08 * (yhi - ylo), 'default', fontsize=7.5,
                color='gray', va='top', ha='left', style='italic')

        # Legend (inside, top-left)
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2,
                  loc='lower left', framealpha=0.95, fontsize=7.5)

        ax.set_title(f'({prob})', loc='left', fontsize=10)

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(OUT_PNG, bbox_inches='tight')
    fig.savefig(OUT_PDF, bbox_inches='tight')
    print(f'Saved {OUT_PNG}')


if __name__ == '__main__':
    main()