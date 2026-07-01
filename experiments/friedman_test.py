"""Friedman test + post-hoc Nemenyi for the main IGD comparison.

Outputs LaTeX table snippets to stdout that can be pasted into results.tex.
"""
import sys
sys.path.insert(0, r'D:\新论文\实验')

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
    """Build (algo, problem) -> list of IGD values."""
    fp = RAW / 'sec_main_v3.json'
    if not fp.exists():
        fp = RAW / 'sec_main_v2.json'
    data = json.load(open(fp, encoding='utf-8'))
    # Merge MOEA/DD
    moeadd_fp = RAW / 'exp4_moeadd.json'
    if moeadd_fp.exists():
        moeadd = json.load(open(moeadd_fp, encoding='utf-8'))
        data.extend(moeadd)
    by_ap = defaultdict(list)
    for r in data:
        if 'igd' in r and np.isfinite(r['igd']) and r['igd'] < 1.0:
            by_ap[(r['algo'], r['problem'])].append(r['igd'])
    return by_ap


def friedman_table():
    by_ap = load_igd()
    # For Friedman: we use only problems where ALL algorithms have data
    # i.e., exclude DF2 (MOEA/DD not there)
    probs_for_test = PROBS_FOR_MOEADD
    n_p, n_a = len(probs_for_test), len(ALGOS)
    mat = np.zeros((n_p, n_a))
    for i, p in enumerate(probs_for_test):
        for j, a in enumerate(ALGOS):
            mat[i, j] = np.mean(by_ap.get((a, p), [np.nan]))

    # Friedman: rank per problem (lower IGD = better = lower rank)
    ranks = np.zeros_like(mat)
    for i in range(n_p):
        ranks[i] = rankdata(mat[i], method='average')

    # Friedman test
    stat, p = friedmanchisquare(*[mat[:, j] for j in range(n_a)])

    # Average ranks per algorithm
    avg_ranks = ranks.mean(axis=0)
    # Critical value for Nemenyi (Bonferroni-like)
    # CD = q_alpha * sqrt(k(k+1) / 6N)
    q_alpha = 2.576  # alpha=0.05, k=6 (from standard Nemenyi tables)
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
