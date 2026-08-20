#!/usr/bin/env python
"""
T62a: Statistical analysis for the n=30 ablation and cross-LLM extensions.

Outputs:
  - Two Nemenyi CD diagrams (fig_nemenyi_ablation.png/pdf, fig_nemenyi_crossllm.png/pdf)
  - Two Friedman test LaTeX tables
  - Wilcoxon T$3$ vs T$0$/T$1$/T$2$ per problem (LaTeX table)
  - Wilcoxon per-problem cross-LLM (LaTeX table)
  - Aggregate "wins/ties/losses" table for T$3$ vs each baseline

Inputs:
  - results/raw/exp7_ablation_combined.json  (1680 rows, 4 versions x 14 problems x 30)
  - results/raw/exp6_cross_llm_n14.json      (1260 rows, 3 LLMs x 14 problems x 30)
"""
from __future__ import annotations
from pathlib import Path
import sys
import json
import math
import shutil
import statistics
import numpy as np
from collections import defaultdict
from scipy.stats import friedmanchisquare, rankdata, wilcoxon
import matplotlib.pyplot as plt
import matplotlib as mpl

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
RAW_DIR   = REPO_ROOT / "results" / "raw"
FIG_DIR   = REPO_ROOT / "results" / "figures"
SUB_DIR   = REPO_ROOT.parent / "论文" / "_submission"
FIG_DIR.mkdir(parents=True, exist_ok=True)
SUB_DIR.mkdir(parents=True, exist_ok=True)

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


def load_median_igd(records, key_field, key_values, problem_field='problem',
                    value_field='igd'):
    """Return (k, N) matrix of median IGD."""
    by_kp = defaultdict(list)
    for r in records:
        if 'error' in r:
            continue
        if value_field not in r:
            continue
        k = r.get(key_field)
        p = r.get(problem_field)
        if k not in key_values or p is None:
            continue
        by_kp[(k, p)].append(r[value_field])
    problems = sorted({p for (k, p) in by_kp},
                      key=lambda x: int(x.replace('DF', '')))
    keys = list(key_values)
    mat = np.zeros((len(problems), len(keys)))
    for i, p in enumerate(problems):
        for j, k in enumerate(keys):
            vals = by_kp.get((k, p), [])
            mat[i, j] = statistics.median(vals) if vals else np.nan
    return mat, problems, keys


def friedman_nemenyi(mat):
    """mat: shape (N problems, k algorithms). Lower better.
    Returns: avg_ranks, stat, p, cd (Nemenyi critical difference)."""
    N, k = mat.shape
    ranks = np.zeros_like(mat)
    for i in range(N):
        ranks[i] = rankdata(mat[i], method='average')
    avg_ranks = ranks.mean(axis=0)
    stat, p = friedmanchisquare(*[mat[:, j] for j in range(k)])
    # Nemenyi q at alpha=0.05, k=4 -> 2.569; k=3 -> 2.343
    q_table = {2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728, 6: 2.850, 7: 2.949}
    q = q_table.get(k, 2.85)
    cd = q * math.sqrt(k * (k + 1) / (6 * N))
    return avg_ranks, stat, p, cd, q


def plot_cd_diagram(sorted_keys, ranks, cd, k, N, title, out_png, out_pdf,
                    color_map, label_map):
    """Draw a Nemenyi CD diagram in the standard Demsar 2006 layout.

    Layout (top to bottom):
      - CD reference bar (top, with endcaps and "CD = X.XX" label)
      - Clique bars (just above the axis, only for cliques of size >= 2)
      - Axis (y=0): solid horizontal line with integer ticks 1..k below
      - Markers: on the axis at their average rank
      - Labels: directly under each marker, with leader lines for
        horizontally-close ranks
    """
    mpl.rcParams.update({
        'font.family': 'DejaVu Serif',
        'font.size': 10,
        'savefig.dpi': 300,
    })
    fig, ax = plt.subplots(figsize=(9.0, 3.0))

    # X axis: always spans the full integer range 0.5 .. k + 0.5 so that
    # the integer ticks are evenly distributed and the CD bar (drawn
    # at the very top) reads naturally as "from rank 1 to rank 1+CD".
    ax.set_xlim(0.5, k + 0.5)
    ax.set_ylim(-1.5, 1.4)
    ax.set_yticks([])

    # Axis line and integer tick labels
    ax.plot([0.5, k + 0.5], [0.0, 0.0], color='black', lw=0.9, zorder=2)
    for x in range(1, k + 1):
        ax.plot([x, x], [0.0, -0.05], color='black', lw=0.9, zorder=2)
    ax.set_xticks(range(1, k + 1))
    ax.set_xticklabels([str(x) for x in range(1, k + 1)], fontsize=10)
    ax.tick_params(axis='x', length=0, pad=4)

    # CD reference bar at the TOP
    cd_y = 1.15
    ax.plot([1, 1 + cd], [cd_y, cd_y], color='black', lw=1.5, zorder=3)
    ax.plot([1, 1], [cd_y - 0.07, cd_y + 0.07], color='black', lw=1.5, zorder=3)
    ax.plot([1 + cd, 1 + cd], [cd_y - 0.07, cd_y + 0.07], color='black', lw=1.5, zorder=3)
    ax.text(1 + cd / 2, cd_y + 0.12, f'CD = {cd:.2f}',
            ha='center', va='bottom', fontsize=10.5, fontweight='bold')

    # Markers: place each on the axis at its rank
    for key, rank in zip(sorted_keys, ranks):
        ax.plot(rank, 0.0, 'o', ms=13, color=color_map[key],
                mec='black', mew=0.9, zorder=4)

    # Use short labels (T0/T1/T2/T3 for ablation, L1/L2/L3 for cross-LLM)
    # to avoid horizontal crowding when ranks are clustered.  Also strip
    # the $...$ math-mode wrapping from label_map so the legend reads
    # as plain text (otherwise mathtext renders "T$0$" as T-sub-0 and
    # the legend ends up with duplicate prefixes).
    short_label_map = {}
    full_label_map = {}
    for k in sorted_keys:
        if k.startswith('V') and '_' in k:
            short = 'T' + k[1]  # V0_baseline -> T0
            short_label_map[k] = short
            # full label: strip $...$ from label_map[k]
            full = label_map[k]
            # replace T$0$ with T0 (the mathtext-wrapped T subscript)
            full = full.replace('T$' + short[-1] + '$', short)
            full_label_map[k] = full
        else:
            llm_short = {
                'qwen2.5:7b': 'L1 (Q2.5)',
                'qwen3.5:9b': 'L2 (Q3.5)',
                'omnicoder-9b': 'L3 (OC)',
            }
            short_label_map[k] = llm_short.get(k, k)
            if short_label_map[k] == k:
                # Fall back: try substring match for the long-form key
                # (e.g. "carstenuhlig/omnicoder-9b:q8_0" -> "L3 (OC)")
                if 'omnicoder' in k:
                    short_label_map[k] = 'L3 (OC)'
                elif 'qwen3.5' in k:
                    short_label_map[k] = 'L2 (Q3.5)'
                elif 'qwen2.5' in k:
                    short_label_map[k] = 'L1 (Q2.5)'
            full_label_map[k] = label_map[k]

    # All labels are placed at the marker's x-position with center anchor;
    # use vertical offset to avoid overlap.  A leader line connects the
    # marker to the label.
    sorted_by_rank = sorted(zip(sorted_keys, ranks), key=lambda kr: kr[1])
    label_y = {}  # key -> y-offset
    y_levels = [-0.40, -0.75, -1.10, -1.45]
    for i, (key, rank) in enumerate(sorted_by_rank):
        placed = False
        for y_off in y_levels:
            collide = False
            for prev_key, (px, py) in label_y.items():
                if abs(rank - px) < 0.40 and abs(y_off - py) < 0.15:
                    collide = True
                    break
            if not collide:
                label_y[key] = (rank, y_off)
                placed = True
                break
        if not placed:
            label_y[key] = (rank, y_levels[0])

    rank_lookup = dict(zip(sorted_keys, ranks))
    for key in sorted_keys:
        x = rank_lookup[key]
        y_off = label_y[key][1]
        # Leader line from the marker to just above the label
        ax.plot([x, x], [-0.05, y_off + 0.05], color='gray', lw=0.6, zorder=2)
        ax.text(x, y_off, short_label_map[key], ha='center', va='top',
                fontsize=11, fontweight='bold')

    # Add a legend mapping short labels to full names BELOW the labels
    legend_handles = []
    for key in sorted_keys:
        legend_handles.append(f"{short_label_map[key]} = {full_label_map[key]}")
    legend_text = "    ".join(legend_handles)
    fig.text(0.5, -0.02, legend_text, ha='center', va='top', fontsize=8.5,
             style='italic')

    # Cliques (groups not significantly different, within CD)
    cliques = []
    cur = [sorted_keys[0]]
    for kk in sorted_keys[1:]:
        if abs(ranks[sorted_keys.index(kk)] - ranks[sorted_keys.index(cur[0])]) <= cd:
            cur.append(kk)
        else:
            cliques.append(cur)
            cur = [kk]
    cliques.append(cur)
    # Clique bars immediately above the axis
    clique_y = 0.20
    for clique in cliques:
        if len(clique) > 1:
            x_min = min(ranks[sorted_keys.index(c)] for c in clique) - 0.04
            x_max = max(ranks[sorted_keys.index(c)] for c in clique) + 0.04
            ax.plot([x_min, x_max], [clique_y, clique_y], color='#aa3322', lw=2.8, zorder=3)
            ax.plot([x_min, x_min], [clique_y - 0.04, clique_y + 0.04], color='#aa3322', lw=2.8)
            ax.plot([x_max, x_max], [clique_y - 0.04, clique_y + 0.04], color='#aa3322', lw=2.8)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.set_xlabel('Average Friedman rank (lower is better)', fontsize=10, labelpad=4)
    fig.suptitle(title, fontsize=10.5, y=1.02)
    fig.tight_layout()
    fig.savefig(out_png, bbox_inches='tight')
    fig.savefig(out_pdf, bbox_inches='tight')
    plt.close(fig)


def ablation_analysis():
    print('\n' + '=' * 60)
    print('ABLATION: 4 versions (T$0$/T$1$/T$2$/T$3$) x 14 problems, n=30 each')
    print('=' * 60)
    data = json.load(open(RAW_DIR / 'exp7_ablation_combined.json',
                          encoding='utf-8'))
    mat, problems, versions = load_median_igd(
        data, 'version', VERSIONS, problem_field='problem')
    print(f'Median-IGD matrix ({mat.shape}):')
    for i, p in enumerate(problems):
        line = f'  {p:<5s}  '
        for j, v in enumerate(versions):
            line += f'{mat[i,j]:.4f}  '
        print(line)

    avg_ranks, stat, p, cd, q = friedman_nemenyi(mat)
    print(f'\nFriedman stat={stat:.3f}, p={p:.6f}, CD={cd:.3f} (q={q})')
    order = np.argsort(avg_ranks)
    for j in order:
        print(f'  {VERSION_LABELS[versions[j]]:<22s}  rank={avg_ranks[j]:.3f}')

    # Nemenyi CD plot
    sorted_keys = [versions[j] for j in order]
    sorted_ranks = [avg_ranks[j] for j in order]
    plot_cd_diagram(sorted_keys, sorted_ranks, cd, len(versions), len(problems),
                    title=f'Nemenyi CD diagram: 4 trigger versions x 14 problems '
                          f'($k$={len(versions)}, $N$={len(problems)}, '
                          f'$n$={30}, $\\alpha$=0.05, $q$={q})',
                    out_png=FIG_DIR / 'fig_nemenyi_ablation.png',
                    out_pdf=FIG_DIR / 'fig_nemenyi_ablation.pdf',
                    color_map=VERSION_COLORS, label_map=VERSION_LABELS)
    print(f'Saved fig_nemenyi_ablation.{{png,pdf}}')
    for ext in ('.png', '.pdf'):
        src = FIG_DIR / f'fig_nemenyi_ablation{ext}'
        dst = SUB_DIR / f'fig_nemenyi_ablation{ext}'
        shutil.copy2(src, dst)
        print(f'  -> {dst}')

    # LaTeX table: Friedman
    out = []
    out.append(r'% ===== AUTO: ablation Friedman table =====')
    out.append(r'\begin{table}[t]')
    out.append(r'\centering')
    out.append(r'\small')
    out.append(r'\caption{Friedman test with Nemenyi post-hoc on the 4 trigger '
               f'versions across 14 CEC 2018 benchmarks ($n=30$ seeds each). '
               f'CD = {cd:.3f} at $\\alpha=0.05$ (Dem\\v{{s}}ar 2006 $q={q}$ '
               f'for $k={len(versions)}$). Versions connected by a bar are '
               r'not significantly different. Median IGD is used for ranking '
               r'to be robust to the catastrophic-failure outliers that '
               r'affect T$2$ and T$3$ on DF2.}')
    out.append(r'\label{tab:friedman-ablation}')
    out.append(r'\begin{tabular}{lcc}')
    out.append(r'\toprule')
    out.append(r'\textbf{Trigger version} & \textbf{Median rank} & \textbf{Mean inv./run} \\')
    out.append(r'\midrule')
    for j in order:
        # mean invocations across 14 problems
        inv_mean = np.mean([np.mean([r['invocations'] for r in data
                                     if r.get('version') == versions[j]
                                     and r.get('problem') == p
                                     and 'error' not in r])
                            for p in problems])
        out.append(f'{VERSION_LABELS[versions[j]]:<22s} & {avg_ranks[j]:.2f} & {inv_mean:.1f} \\\\')
    out.append(r'\bottomrule')
    out.append(r'\end{tabular}')
    out.append(r'\end{table}')
    out.append(f'% Friedman stat = {stat:.3f}, p = {p:.6f}')
    out.append('')
    tex_path = REPO_ROOT / 'tex_stats_ablation_friedman.tex'
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    print(f'Saved {tex_path}')

    # Wilcoxon: T$3$ vs each of T$0$/T$1$/T$2$ (paired, n=30 per problem)
    out2 = []
    out2.append(r'% ===== AUTO: Wilcoxon T$3$ vs T$0$/T$1$/T$2$ per problem =====')
    out2.append(r'\begin{table}[t]')
    out2.append(r'\centering')
    out2.append(r'\small')
    out2.append(r'\caption{Paired Wilcoxon signed-rank test (T$3$ vs T$0$/T$1$/T$2$) on the 14 CEC 2018 '
                 'benchmarks ($n=30$ seeds per problem). $p<0.05$ is significant; '
                 'W+ = Wilcoxon signed-rank statistic (sum of positive ranks); '
                 'Cohen\'s $d$ is the paired effect size. '
                 'T$3$ < T$x$ means T$3$ has the lower (better) median IGD.}')
    out2.append(r'\label{tab:wilcoxon-ablation}')
    out2.append(r'\begin{tabular}{l' + 'ccc' * 3 + '}')
    out2.append(r'\toprule')
    out2.append(r' & \multicolumn{3}{c}{T$3$ vs T$0$ (always-trigger)} & '
                 r'\multicolumn{3}{c}{T$3$ vs T$1$ (entropy)} & '
                 r'\multicolumn{3}{c}{T$3$ vs T$2$ (entr+stag)} \\')
    out2.append(r'\cmidrule(lr){2-4}\cmidrule(lr){5-7}\cmidrule(lr){8-10}')
    out2.append(r'Problem & $p$ & W+ & $d$ & $p$ & W+ & $d$ & $p$ & W+ & $d$ \\')
    out2.append(r'\midrule')
    n_sig_v3 = {0: 0, 1: 0, 2: 0}
    n_sig_other = {0: 0, 1: 0, 2: 0}
    for p in problems:
        cells = []
        v3 = sorted([r['igd'] for r in data
                     if r.get('version') == 'V3_triple'
                     and r.get('problem') == p and 'error' not in r])
        for vi, ver in enumerate(['V0_baseline', 'V1_single', 'V2_double']):
            other = sorted([r['igd'] for r in data
                            if r.get('version') == ver
                            and r.get('problem') == p and 'error' not in r])
            assert len(v3) == len(other) == 30
            try:
                wstat, pval = wilcoxon(v3, other, alternative='two-sided')
                diff = np.array(v3) - np.array(other)
                d = diff.mean() / diff.std(ddof=1) if diff.std(ddof=1) > 0 else 0
                if pval < 0.05:
                    if d < 0:
                        n_sig_v3[vi] += 1
                    else:
                        n_sig_other[vi] += 1
                cells.append(f'{pval:.4f} & {int(wstat)} & {d:+.2f}')
            except ValueError as e:
                cells.append(f'-- & -- & --')
        out2.append(f'{p:<5s} & ' + ' & '.join(cells) + r' \\')
    out2.append(r'\midrule')
    summary = f"T$3$ wins (sig.): {n_sig_v3[0]}/{len(problems)} vs T$0$, "\
              f"{n_sig_v3[1]}/{len(problems)} vs T$1$, {n_sig_v3[2]}/{len(problems)} vs T$2$ "\
              f"| Baseline wins: {n_sig_other[0]}/{len(problems)}, {n_sig_other[1]}, {n_sig_other[2]}"
    out2.append(r'\bottomrule')
    out2.append(r'\end{tabular}')
    out2.append(r'\end{table}')
    out2.append(f'% {summary}')
    tex_path2 = REPO_ROOT / 'tex_stats_ablation_wilcoxon.tex'
    with open(tex_path2, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out2))
    print(f'Saved {tex_path2}')
    print(summary)

    return {
        'mat': mat, 'problems': problems, 'avg_ranks': avg_ranks,
        'cd': cd, 'q': q, 'stat': stat, 'p': p,
        'wilcoxon_summary': summary,
    }


def crossllm_analysis():
    print('\n' + '=' * 60)
    print('CROSS-LLM: 3 LLMs x 14 problems, n=30 each')
    print('=' * 60)
    data = json.load(open(RAW_DIR / 'exp6_cross_llm_n14.json', encoding='utf-8'))
    mat, problems, llms = load_median_igd(
        data, 'model', LLMS, problem_field='prob')
    print(f'Median-IGD matrix ({mat.shape}):')
    for i, p in enumerate(problems):
        line = f'  {p:<5s}  '
        for j, llm in enumerate(llms):
            line += f'{mat[i,j]:.4f}  '
        print(line)

    avg_ranks, stat, p, cd, q = friedman_nemenyi(mat)
    print(f'\nFriedman stat={stat:.3f}, p={p:.6f}, CD={cd:.3f} (q={q})')
    order = np.argsort(avg_ranks)
    for j in order:
        print(f'  {LLM_LABELS[llms[j]]:<28s}  rank={avg_ranks[j]:.3f}')

    sorted_keys = [llms[j] for j in order]
    sorted_ranks = [avg_ranks[j] for j in order]
    plot_cd_diagram(sorted_keys, sorted_ranks, cd, len(llms), len(problems),
                    title=f'Nemenyi CD diagram: 3 LLM families x 14 problems '
                          f'($k$={len(llms)}, $N$={len(problems)}, '
                          f'$n$={30}, $\\alpha$=0.05, $q$={q})',
                    out_png=FIG_DIR / 'fig_nemenyi_crossllm.png',
                    out_pdf=FIG_DIR / 'fig_nemenyi_crossllm.pdf',
                    color_map=LLM_COLORS, label_map=LLM_LABELS)
    print(f'Saved fig_nemenyi_crossllm.{{png,pdf}}')
    for ext in ('.png', '.pdf'):
        src = FIG_DIR / f'fig_nemenyi_crossllm{ext}'
        dst = SUB_DIR / f'fig_nemenyi_crossllm{ext}'
        shutil.copy2(src, dst)
        print(f'  -> {dst}')

    # LaTeX table
    out = []
    out.append(r'% ===== AUTO: cross-LLM Friedman table =====')
    out.append(r'\begin{table}[t]')
    out.append(r'\centering')
    out.append(r'\small')
    out.append(r'\caption{Friedman test with Nemenyi post-hoc on the 3 LLM families '
               f'across 14 CEC 2018 benchmarks ($n=30$ seeds each). CD = {cd:.3f} '
               f'at $\\alpha=0.05$ (Dem\\v{{s}}ar 2006 $q={q}$ for $k={len(llms)}$). '
               r'LLMs connected by a bar are not significantly different.}')
    out.append(r'\label{tab:friedman-crossllm}')
    out.append(r'\begin{tabular}{lc}')
    out.append(r'\toprule')
    out.append(r'\textbf{LLM family} & \textbf{Median rank} \\')
    out.append(r'\midrule')
    for j in order:
        out.append(f'{LLM_LABELS[llms[j]]:<28s} & {avg_ranks[j]:.2f} \\\\')
    out.append(r'\bottomrule')
    out.append(r'\end{tabular}')
    out.append(r'\end{table}')
    out.append(f'% Friedman stat = {stat:.3f}, p = {p:.6f}')
    out.append('')
    tex_path = REPO_ROOT / 'tex_stats_crossllm_friedman.tex'
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    print(f'Saved {tex_path}')

    # Wilcoxon per problem: qwen2.5 vs qwen3.5, qwen2.5 vs omnicoder, qwen3.5 vs omnicoder
    out2 = []
    out2.append(r'% ===== AUTO: Wilcoxon per-problem cross-LLM =====')
    out2.append(r'\begin{table}[t]')
    out2.append(r'\centering')
    out2.append(r'\scriptsize')
    out2.append(r'\caption{Paired Wilcoxon signed-rank tests between the 3 LLM '
                 'families on each of the 14 CEC 2018 benchmarks ($n=30$ seeds). '
                 'Bonferroni-corrected threshold $\\alpha=0.05/3=0.0167$. '
                 'W+ = Wilcoxon signed-rank statistic (sum of positive ranks). '
                 'Cohen\'s $d$ is the paired effect size (negative = first LLM '
                 'wins).}')
    out2.append(r'\label{tab:wilcoxon-crossllm}')
    out2.append(r'\begin{tabular}{l' + 'ccc' * 3 + '}')
    out2.append(r'\toprule')
    out2.append(r' & \multicolumn{3}{c}{qwen2.5 vs qwen3.5} & '
                 r'\multicolumn{3}{c}{qwen2.5 vs omnicoder} & '
                 r'\multicolumn{3}{c}{qwen3.5 vs omnicoder} \\')
    out2.append(r'\cmidrule(lr){2-4}\cmidrule(lr){5-7}\cmidrule(lr){8-10}')
    out2.append(r'Prob. & $p$ & W+ & $d$ & $p$ & W+ & $d$ & $p$ & W+ & $d$ \\')
    out2.append(r'\midrule')
    for prob in problems:
        cells = []
        a = sorted([r['igd'] for r in data
                    if r.get('model') == 'qwen2.5:7b'
                    and r.get('prob') == prob and 'error' not in r])
        b = sorted([r['igd'] for r in data
                    if r.get('model') == 'qwen3.5:9b'
                    and r.get('prob') == prob and 'error' not in r])
        c = sorted([r['igd'] for r in data
                    if r.get('model') == 'carstenuhlig/omnicoder-9b:q8_0'
                    and r.get('prob') == prob and 'error' not in r])
        for x, y in [(a, b), (a, c), (b, c)]:
            try:
                wstat, pval = wilcoxon(x, y, alternative='two-sided')
                diff = np.array(x) - np.array(y)
                d = diff.mean() / diff.std(ddof=1) if diff.std(ddof=1) > 0 else 0
                cells.append(f'{pval:.4f} & {int(wstat)} & {d:+.2f}')
            except ValueError:
                cells.append(f'-- & -- & --')
        out2.append(f'{prob:<5s} & ' + ' & '.join(cells) + r' \\')
    out2.append(r'\bottomrule')
    out2.append(r'\end{tabular}')
    out2.append(r'\end{table}')
    tex_path2 = REPO_ROOT / 'tex_stats_crossllm_wilcoxon.tex'
    with open(tex_path2, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out2))
    print(f'Saved {tex_path2}')

    return {'mat': mat, 'problems': problems, 'avg_ranks': avg_ranks, 'cd': cd}


if __name__ == '__main__':
    ablation_analysis()
    crossllm_analysis()
