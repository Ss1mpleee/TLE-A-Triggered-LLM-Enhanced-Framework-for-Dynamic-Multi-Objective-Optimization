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

"""Friedman test + post-hoc Nemenyi for the main IGD comparison.

Outputs LaTeX table snippets to stdout that can be pasted into results.tex.
"""
import json
import numpy as np
from pathlib import Path
from collections import defaultdict
from scipy.stats import friedmanchisquare, rankdata

RAW = Path(r'D:\新论文\实验\results\raw')

ALGOS = ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A', 'MOEA/DD', 'TLE']
PROBS = ['DF1', 'DF2', 'DF3', 'DF5', 'DF7']
PROBS_FOR_MOEADD = ['DF1', 'DF3', 'DF5', 'DF7']  # exclude DF2


def load_igd():
    """Build (algo, problem) -> list of IGD values.

    We do NOT pre-filter the catastrophic MOEA/DD DF2 entries here: the
    imputation is applied inside `friedman_table()` where we know which
    (algo, problem) cell needs the imputation.
    """
    fp = RAW / 'sec_main_v3.json'
    if not fp.exists():
        fp = RAW / 'sec_main_v2.json'
    data = json.load(open(fp, encoding='utf-8'))
    # Backwards-compatibility: if the older exp4_moeadd.json has additional
    # entries (it shouldn't — sec_main_v3.json already includes MOEA/DD),
    # merge them in.
    moeadd_fp = RAW / 'exp4_moeadd.json'
    if moeadd_fp.exists():
        moeadd = json.load(open(moeadd_fp, encoding='utf-8'))
        existing = {(d['algo'], d['problem'], d['seed'])
                    for d in data if d['algo'] == 'MOEA/DD'}
        data.extend(d for d in moeadd
                    if (d['algo'], d['problem'], d['seed']) not in existing)
    by_ap = defaultdict(list)
    for r in data:
        if 'igd' in r and np.isfinite(r['igd']):
            by_ap[(r['algo'], r['problem'])].append(r['igd'])
    return by_ap


def friedman_table():
    """Friedman + Nemenyi on the IGD metric.

    All 5 CEC 2018 problems are used. MOEA/DD's DF2 entry is imputed as
    the mean of its ranks on the other 4 problems (its 8 raw DF2 IGDs
    are catastrophic, of order 1e7 to 1e27).
    """
    by_ap = load_igd()
    n_p, n_a = len(PROBS), len(ALGOS)
    mat = np.zeros((n_p, n_a))
    moeadd_idx = ALGOS.index('MOEA/DD')
    df2_idx = PROBS.index('DF2')

    for i, p in enumerate(PROBS):
        for j, a in enumerate(ALGOS):
            vals = by_ap.get((a, p), [])
            if a == 'MOEA/DD' and p == 'DF2':
                # Will be imputed below; mark with NaN for now.
                mat[i, j] = np.nan
            else:
                mat[i, j] = np.mean(vals) if vals else np.nan

    # First pass: rank per problem (lower IGD = better = lower rank).
    # We rank the 5 valid (non-NaN) entries; the NaN entry will be
    # imputed in a second pass once all other problems have been ranked.
    ranks = np.zeros((n_p, n_a))
    for i in range(n_p):
        valid_mask = ~np.isnan(mat[i])
        if valid_mask.sum() < n_a:
            # Some NaN: rank only the valid entries.
            ranks[i, valid_mask] = rankdata(mat[i, valid_mask], method='average')
        else:
            ranks[i] = rankdata(mat[i], method='average')

    # Second pass: impute MOEA/DD's DF2 entry as the mean of its ranks
    # on the other 4 problems.
    if np.isnan(mat[df2_idx, moeadd_idx]):
        other_ranks = [ranks[k, moeadd_idx]
                       for k in range(n_p) if k != df2_idx]
        ranks[df2_idx, moeadd_idx] = float(np.mean(other_ranks))

    # Friedman test: only over the 4 problems where every algorithm has
    # finite IGD (the 5th problem, DF2, has the imputed MOEA/DD entry
    # which is not a "real" measurement and so is excluded from the test
    # statistic).  This is the standard Demšar (2006) treatment.
    valid_probs = [p for j, p in enumerate(PROBS) if j != df2_idx]
    valid_mat = np.array([[np.mean(by_ap.get((a, p), [np.nan]))
                           for a in ALGOS] for p in valid_probs])
    stat, p = friedmanchisquare(*[valid_mat[:, j] for j in range(n_a)])

    # Average ranks per algorithm (over the 5 problems, with imputation)
    avg_ranks = ranks.mean(axis=0)
    # Critical value for Nemenyi (Bonferroni-like)
    # CD = q_alpha * sqrt(k(k+1) / 6N),  with N=5 (the imputed DF2 is
    # part of the ranking but the test statistic itself uses 4 problems).
    q_alpha = 2.85  # alpha=0.05, k=6 (from Demsar 2006 Table 5b)
    N = n_p
    k = n_a
    cd = q_alpha * np.sqrt(k * (k + 1) / (6 * N))

    print("% ============ AUTO-GENERATED Friedman test table ============")
    print(r"\begin{table}[t]")
    print(r"\centering")
    print(r"\caption{Friedman test with post-hoc Nemenyi procedure on the 5 DMO benchmarks. "
          "Lower mean rank = better. Critical difference (CD) at $\alpha=0.05$ "
          f"is {cd:.3f}. Algorithms connected by a horizontal bar are not "
          "significantly different.}")
    print(r"\label{tab:friedman}")
    print(r"\begin{tabular}{lcc}")
    print(r"\toprule")
    print(r"\textbf{Algorithm} & \textbf{Mean rank} & \textbf{Group (Nemenyi CD)} \\")
    print(r"\midrule")

    # Sort by rank
    order = np.argsort(avg_ranks)
    sorted_algos = [ALGOS[i] for i in order]
    sorted_ranks = avg_ranks[order]

    for i, (a, r) in enumerate(zip(sorted_algos, sorted_ranks)):
        bar_start = r
        bar_end = r
        for j, (a2, r2) in enumerate(zip(sorted_algos, sorted_ranks)):
            if abs(r - r2) < cd:
                bar_end = max(bar_end, r2)
                bar_start = min(bar_start, r2)
        print(f"{a:25s} & {r:.2f} & [{bar_start:.2f}, {bar_end:.2f}] \\\\")

    print(r"\bottomrule")
    print(r"\end{tabular}")
    print(r"\end{table}")
    print()
    print(f"% Friedman statistic: {stat:.3f}, p-value: {p:.6f}")
    if p < 0.05:
        print("% Friedman test is significant: at least one algorithm differs.")
    else:
        print("% Friedman test is NOT significant: no significant difference detected.")


def hv_table():
    """Same for HV (higher is better -> rank ascending)."""
    fp = RAW / 'sec_main_v3.json'
    if not fp.exists():
        fp = RAW / 'sec_main_v2.json'
    data = json.load(open(fp, encoding='utf-8'))
    by_ap = defaultdict(list)
    for r in data:
        if 'hv' in r and np.isfinite(r['hv']):
            by_ap[(r['algo'], r['problem'])].append(r['hv'])

    n_p, n_a = len(PROBS), len(ALGOS)
    mat = np.zeros((n_p, n_a))
    for i, p in enumerate(PROBS):
        for j, a in enumerate(ALGOS):
            mat[i, j] = np.mean(by_ap.get((a, p), [0]))

    ranks = np.zeros_like(mat)
    # HV: higher is better -> negate to make lower = better for rankdata
    for i in range(n_p):
        ranks[i] = rankdata(-mat[i], method='average')

    stat, p = friedmanchisquare(*[mat[:, j] for j in range(n_a)])
    avg_ranks = ranks.mean(axis=0)
    q_alpha = 2.728
    N = n_p
    k = n_a
    cd = q_alpha * np.sqrt(k * (k + 1) / (6 * N))

    print("% ============ AUTO-GENERATED Friedman test table for HV ============")
    print(r"\begin{table}[t]")
    print(r"\centering")
    print(r"\caption{Friedman test on the HV metric. Lower rank = better (higher HV).}")
    print(r"\label{tab:friedman_hv}")
    print(r"\begin{tabular}{lc}")
    print(r"\toprule")
    print(r"\textbf{Algorithm} & \textbf{Mean rank} \\")
    print(r"\midrule")
    order = np.argsort(avg_ranks)
    for i in order:
        print(f"{ALGOS[i]:25s} & {avg_ranks[i]:.2f} \\\\")
    print(r"\bottomrule")
    print(r"\end{tabular}")
    print(r"\end{table}")
    print(f"% HV Friedman: stat={stat:.3f}, p={p:.6f}, CD={cd:.3f}")


if __name__ == "__main__":
    friedman_table()
    print()
    hv_table()
