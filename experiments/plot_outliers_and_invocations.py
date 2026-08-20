#!/usr/bin/env python
"""
T62b: Additional figures for ablation + cross-LLM.

Outputs:
  - fig_df2_outlier.png/pdf  : DF2 IGD distribution violin plot, 3 LLMs
  - fig_invocation_heatmap.png/pdf : invocation count heatmap, 4 versions x 14 problems
  - fig_critical_cases.png/pdf : 2x2 box plot of IGD on DF1, DF2, DF11, DF14 for both analyses

Reads:
  - results/raw/exp7_ablation_combined.json  (1680 rows)
  - results/raw/exp6_cross_llm_n14.json      (1260 rows)
"""
from __future__ import annotations
from pathlib import Path
import sys
import json
import shutil
import statistics
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import matplotlib as mpl

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
RAW_DIR   = REPO_ROOT / "results" / "raw"
FIG_DIR   = REPO_ROOT / "results" / "figures"
SUB_DIR   = REPO_ROOT.parent / "论文" / "_submission"
FIG_DIR.mkdir(parents=True, exist_ok=True)
SUB_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 11
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 9
sns.set_style('whitegrid')

VERSIONS = ['V0_baseline', 'V1_single', 'V2_double', 'V3_triple']
VERSION_LABELS = {
    'V0_baseline': 'T$0$ (always, cap=50)',
    'V1_single':   'T$1$ (entropy only)',
    'V2_double':   'T$2$ (entropy+stagnation)',
    'V3_triple':   'T$3$ (proposed: triple)',
}
VERSION_COLORS = {
    'V0_baseline': '#9aa3a8',
    'V1_single':   '#7eb6d9',
    'V2_double':   '#4ca28a',
    'V3_triple':   '#e8763a',
}
LLMS = ['qwen2.5:7b', 'qwen3.5:9b', 'carstenuhlig/omnicoder-9b:q8_0']
LLM_LABELS = {
    'qwen2.5:7b': 'qwen2.5:7b (chat)',
    'qwen3.5:9b': 'qwen3.5:9b (chat)',
    'carstenuhlig/omnicoder-9b:q8_0': 'omnicoder-9b (code)',
}
LLM_COLORS = {
    'qwen2.5:7b': '#e8763a',
    'qwen3.5:9b': '#7eb6d9',
    'carstenuhlig/omnicoder-9b:q8_0': '#9aa3a8',
}


# ============================================================================
# Figure 1: DF2 IGD distribution violin/box plot, 3 LLMs
# ============================================================================
def fig_df2_outlier():
    data = json.load(open(RAW_DIR / 'exp6_cross_llm_n14.json', encoding='utf-8'))
    by_llm = defaultdict(list)
    for r in data:
        if r.get('prob') == 'DF2' and 'error' not in r:
            by_llm[r['model']].append(r['igd'])

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    # Left: full range (log y)
    ax = axes[0]
    data_for_violin = [sorted(by_llm[m]) for m in LLMS]
    parts = ax.violinplot(data_for_violin, showmedians=True, showextrema=True)
    for pc, m in zip(parts['bodies'], LLMS):
        pc.set_facecolor(LLM_COLORS[m])
        pc.set_edgecolor('black')
        pc.set_alpha(0.7)
    ax.set_xticks(range(1, len(LLMS) + 1))
    ax.set_xticklabels([LLM_LABELS[m] for m in LLMS], rotation=15, ha='right')
    ax.set_yscale('log')
    ax.set_ylabel('IGD on DF2 (log scale, n=30 seeds)')
    ax.set_title('DF2 IGD distribution per LLM (log y, full range)')
    ax.grid(axis='y', alpha=0.3)

    # Right: clipped at 5 to see bimodal structure clearly
    ax = axes[1]
    clipped = [[min(v, 5.0) for v in sorted(by_llm[m])] for m in LLMS]
    parts = ax.violinplot(clipped, showmedians=True, showextrema=True)
    for pc, m in zip(parts['bodies'], LLMS):
        pc.set_facecolor(LLM_COLORS[m])
        pc.set_edgecolor('black')
        pc.set_alpha(0.7)
    ax.set_xticks(range(1, len(LLMS) + 1))
    ax.set_xticklabels([LLM_LABELS[m] for m in LLMS], rotation=15, ha='right')
    ax.set_ylabel('IGD on DF2 (clipped at 5, n=30 seeds)')
    ax.set_title('DF2 IGD distribution per LLM (clipped at 5, bimodal visible)')
    ax.grid(axis='y', alpha=0.3)

    fig.suptitle('Cross-LLM stress test on DF2: qwen2.5 catastrophic vs. '
                 'qwen3.5/omnicoder bimodal', fontsize=12, y=1.02)
    plt.tight_layout()
    out = FIG_DIR / 'fig_df2_outlier.png'
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.savefig(out.with_suffix('.pdf'), bbox_inches='tight')
    plt.close()
    print(f'Saved {out} + .pdf')
    for ext in ('.png', '.pdf'):
        shutil.copy2(FIG_DIR / f'fig_df2_outlier{ext}',
                     SUB_DIR / f'fig_df2_outlier{ext}')


# ============================================================================
# Figure 2: Invocation count heatmap, 4 versions x 14 problems
# ============================================================================
def fig_invocation_heatmap():
    data = json.load(open(RAW_DIR / 'exp7_ablation_combined.json', encoding='utf-8'))
    by_vp = defaultdict(list)
    for r in data:
        if 'error' in r: continue
        by_vp[(r.get('version'), r.get('problem'))].append(r['invocations'])

    probs = sorted({p for (v, p) in by_vp}, key=lambda x: int(x.replace('DF', '')))
    mat = np.zeros((len(VERSIONS), len(probs)))
    for i, v in enumerate(VERSIONS):
        for j, p in enumerate(probs):
            mat[i, j] = np.mean(by_vp[(v, p)])

    fig, ax = plt.subplots(figsize=(13, 3.0))
    im = ax.imshow(mat, aspect='auto', cmap='YlOrRd', vmin=0, vmax=50)
    ax.set_xticks(range(len(probs)))
    ax.set_yticks(range(len(VERSIONS)))
    ax.set_xticklabels(probs)
    ax.set_yticklabels([VERSION_LABELS[v] for v in VERSIONS])
    ax.set_xlabel('CEC 2018 DMO problem')
    ax.set_title('LLM invocation count per run (mean, n=30) — T$1$/T$2$ sparse, '
                 'T$3$ moderate, T$0$ always')

    for i in range(len(VERSIONS)):
        for j in range(len(probs)):
            v = mat[i, j]
            cnorm = v / 50.0
            text_color = 'white' if cnorm > 0.55 else 'black'
            ax.text(j, i, f'{v:.1f}', ha='center', va='center',
                    color=text_color, fontsize=8)
    cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label('mean LLM calls / run')
    plt.tight_layout()
    out = FIG_DIR / 'fig_invocation_heatmap.png'
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.savefig(out.with_suffix('.pdf'), bbox_inches='tight')
    plt.close()
    print(f'Saved {out} + .pdf')
    for ext in ('.png', '.pdf'):
        shutil.copy2(FIG_DIR / f'fig_invocation_heatmap{ext}',
                     SUB_DIR / f'fig_invocation_heatmap{ext}')


# ============================================================================
# Figure 3: Critical-case 2x2 boxplot (DF1, DF2, DF11, DF14)
# Ablation lite (4 versions) on top row, Cross-LLM (3 LLMs) on bottom row.
# ============================================================================
def fig_critical_cases():
    abl = json.load(open(RAW_DIR / 'exp7_ablation_combined.json', encoding='utf-8'))
    clm = json.load(open(RAW_DIR / 'exp6_cross_llm_n14.json', encoding='utf-8'))

    crit_probs = ['DF1', 'DF2', 'DF11', 'DF14']
    fig, axes = plt.subplots(2, 4, figsize=(16, 7))

    for col, prob in enumerate(crit_probs):
        # Top row: ablation
        ax = axes[0, col]
        positions = []
        data_boxes = []
        colors = []
        for vi, ver in enumerate(VERSIONS):
            vals = [r['igd'] for r in abl
                    if r.get('version') == ver and r.get('problem') == prob
                    and 'error' not in r]
            if not vals: continue
            data_boxes.append(vals)
            positions.append(vi + 1)
            colors.append(VERSION_COLORS[ver])
        bp = ax.boxplot(data_boxes, positions=positions, widths=0.6,
                        patch_artist=True, showfliers=False,
                        medianprops=dict(color='black', linewidth=1.2))
        for patch, c in zip(bp['boxes'], colors):
            patch.set_facecolor(c); patch.set_alpha(0.85)
            patch.set_edgecolor('black'); patch.set_linewidth(0.6)
        ax.set_xticks(positions)
        ax.set_xticklabels([VERSION_LABELS[v] for v in VERSIONS],
                           rotation=30, ha='right', fontsize=8)
        ax.set_title(f'{prob} — ablation')
        # DF14 (all-zero) cannot be log-scaled; use linear with a
        # small ylim so the "0.0 on all 30 seeds" annotation is
        # visible.  All other panels use log scale.
        if prob == 'DF14':
            ax.set_yscale('linear')
            ax.set_ylim(-0.05, 0.5)
        else:
            ax.set_yscale('log')
        ax.grid(axis='y', alpha=0.3)
        if col == 0:
            ax.set_ylabel('IGD (log scale)')

        # Bottom row: cross-llm
        ax = axes[1, col]
        positions = []
        data_boxes = []
        colors = []
        for li, llm in enumerate(LLMS):
            vals = [r['igd'] for r in clm
                    if r.get('model') == llm and r.get('prob') == prob
                    and 'error' not in r]
            if not vals: continue
            data_boxes.append(vals)
            positions.append(li + 1)
            colors.append(LLM_COLORS[llm])
        bp = ax.boxplot(data_boxes, positions=positions, widths=0.6,
                        patch_artist=True, showfliers=False,
                        medianprops=dict(color='black', linewidth=1.2))
        for patch, c in zip(bp['boxes'], colors):
            patch.set_facecolor(c); patch.set_alpha(0.85)
            patch.set_edgecolor('black'); patch.set_linewidth(0.6)
        ax.set_xticks(positions)
        ax.set_xticklabels([LLM_LABELS[m] for m in LLMS],
                           rotation=15, ha='right', fontsize=8)
        ax.set_title(f'{prob} — cross-LLM')
        if prob == 'DF14':
            ax.set_yscale('linear')
            ax.set_ylim(-0.05, 0.5)
        else:
            ax.set_yscale('log')
        ax.grid(axis='y', alpha=0.3)
        if col == 0:
            ax.set_ylabel('IGD (log scale)')

    # Annotations: explain the 2 visually "empty" panels (DF11 failure
    # floor, DF14 all-zero).  Without these, readers may think the
    # data is missing.  Both are real and important findings, not bugs.
    for col, prob in enumerate(crit_probs):
        if prob == 'DF11':
            # All 4 ablation versions and all 3 LLMs lock at IGD >= 1.0
            for row in range(2):
                ax = axes[row, col]
                ax.text(0.5, 0.5,
                        '3-obj failure floor:\nIGD $\\geq$ 1.0 on all 30 seeds',
                        transform=ax.transAxes, ha='center', va='center',
                        fontsize=8.5, color='#444444', style='italic',
                        bbox=dict(boxstyle='round,pad=0.3',
                                  facecolor='#eeeeee', edgecolor='#888888',
                                  alpha=0.85))
        elif prob == 'DF14':
            # All 4 ablation versions and all 3 LLMs reach IGD = 0.0
            for row in range(2):
                ax = axes[row, col]
                ax.text(0.5, 0.5,
                        '3-obj success case:\nIGD = 0.0 on all 30 seeds',
                        transform=ax.transAxes, ha='center', va='center',
                        fontsize=8.5, color='#226622', style='italic',
                        bbox=dict(boxstyle='round,pad=0.3',
                                  facecolor='#eeffee', edgecolor='#88aa88',
                                  alpha=0.85))

    # Add a top-row note (just above the panel titles, BELOW the
    # suptitle) explaining the 4-DF selection.
    fig.text(0.5, 0.965,
             '4 of 14 problems: DF1 (simple 2-obj), DF2 (catastrophic 2-obj), '
             'DF11 (3-obj failure floor), DF14 (3-obj success). '
             'Full 14-problem ablation: Fig.~S6. Full 14-problem cross-LLM: Fig.~S8.',
             ha='center', va='top', fontsize=8, style='italic', color='#555555')

    fig.suptitle('Critical-case IGD boxplots: ablation (top) vs cross-LLM '
                 '(bottom), n=30 each', fontsize=12, y=0.995)
    plt.tight_layout()
    out = FIG_DIR / 'fig_critical_cases.png'
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.savefig(out.with_suffix('.pdf'), bbox_inches='tight')
    plt.close()
    print(f'Saved {out} + .pdf')
    for ext in ('.png', '.pdf'):
        shutil.copy2(FIG_DIR / f'fig_critical_cases{ext}',
                     SUB_DIR / f'fig_critical_cases{ext}')


if __name__ == '__main__':
    fig_df2_outlier()
    fig_invocation_heatmap()
    fig_critical_cases()
