"""
Re-plot all figures from v2 data.
Outputs to D:\新论文\论文\figures\ (which the .tex references as ./figures/).
"""
import sys
sys.path.insert(0, r'D:\新论文\实验')
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict

RAW = Path(r'D:\新论文\实验\results\raw')
FIG = Path(r'D:\新论文\论文\figures')
FIG.mkdir(parents=True, exist_ok=True)

ALGOS = ['DE', 'DE-LM-static-trigger', 'PPS-DMOEA', 'DNSGA-II-A', 'TLE']
PROBS = ['DF1', 'DF2', 'DF3', 'DF5', 'DF7']
COLORS = ['#7f7f7f', '#17becf', '#9467bd', '#2ca02c', '#d62728']


def load_main():
    return json.load(open(RAW / 'sec_main_v2.json', encoding='utf-8'))


def load_abl():
    return json.load(open(RAW / 'sec_ablation_v2.json', encoding='utf-8'))


def load_uav():
    return json.load(open(RAW / 'exp3_uav_v2.json', encoding='utf-8'))


# ============ Fig 1: Main IGD bar chart (5 algos × 5 probs) ============
def plot_main_igd():
    data = load_main()
    by_ap = defaultdict(list)
    for r in data:
        if 'igd' in r and np.isfinite(r['igd']):
            by_ap[(r['algo'], r['problem'])].append(r['igd'])

    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(PROBS))
    width = 0.16
    for i, algo in enumerate(ALGOS):
        means = [np.mean(by_ap.get((algo, p), [np.nan])) for p in PROBS]
        stds = [np.std(by_ap.get((algo, p), [0])) for p in PROBS]
        ax.bar(x + (i - 2) * width, means, width, yerr=stds,
               label=algo, color=COLORS[i], alpha=0.85, capsize=3)
    ax.set_xticks(x)
    ax.set_xticklabels(PROBS)
    ax.set_ylabel('IGD (lower = better)')
    ax.set_xlabel('CEC 2018 Dynamic Multi-Objective Benchmark')
    ax.set_title('Main Comparison: 5 Algorithms × 5 Problems × 5 Seeds × 200 Generations')
    ax.legend(loc='upper left', fontsize=9, ncol=2)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIG / 'fig_main_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved fig_main_comparison.png')


# ============ Fig 2: HV bar chart ============
def plot_main_hv():
    data = load_main()
    by_ap = defaultdict(list)
    for r in data:
        if 'hv' in r and np.isfinite(r['hv']):
            by_ap[(r['algo'], r['problem'])].append(r['hv'])

    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(PROBS))
    width = 0.16
    for i, algo in enumerate(ALGOS):
        means = [np.mean(by_ap.get((algo, p), [np.nan])) for p in PROBS]
        stds = [np.std(by_ap.get((algo, p), [0])) for p in PROBS]
        ax.bar(x + (i - 2) * width, means, width, yerr=stds,
               label=algo, color=COLORS[i], alpha=0.85, capsize=3)
    ax.set_xticks(x)
    ax.set_xticklabels(PROBS)
    ax.set_ylabel('HV (higher = better)')
    ax.set_xlabel('CEC 2018 Problem')
    ax.set_title('Hypervolume Comparison')
    ax.legend(loc='lower right', fontsize=9, ncol=2)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIG / 'fig_hv_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved fig_hv_comparison.png')


# ============ Fig 3: Ablation (4 variants × 2 probs) ============
def plot_ablation():
    data = load_abl()
    by_vp = defaultdict(list)
    for r in data:
        if 'igd' in r and np.isfinite(r['igd']):
            by_vp[(r['variant'], r['problem'])].append(r['igd'])

    variants = ['V0_TLE_full', 'V1_single_signal', 'V2_heuristic_budget', 'V3_no_llm']
    short_names = ['V0: TLE full\n(bandit)', 'V1: single-signal\n(only entropy)',
                   'V2: heuristic\nbudget', 'V3: no LLM\n(pure DE)']
    probs = ['DF1', 'DF5']
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    x = np.arange(len(variants))
    width = 0.35
    for ax_i, p in enumerate(probs):
        for vi, v in enumerate(variants):
            vals = by_vp.get((v, p), [np.nan])
            m = np.mean(vals)
            s = np.std(vals)
            axes[ax_i].bar(vi, m, yerr=s, color=COLORS[vi], alpha=0.85, capsize=4, width=width)
            axes[ax_i].text(vi, m + s + 0.02 * max(1, m), f'{m:.3f}', ha='center', fontsize=8)
        axes[ax_i].set_xticks(x)
        axes[ax_i].set_xticklabels(short_names, fontsize=8)
        axes[ax_i].set_ylabel('IGD (lower = better)')
        axes[ax_i].set_title(f'({chr(ord("a") + ax_i)}) {p}')
        axes[ax_i].grid(axis='y', alpha=0.3)
    fig.suptitle('Ablation Study: 4 Variants × DF1+DF5 × 5 Seeds', fontsize=12, y=1.02)
    plt.tight_layout()
    plt.savefig(FIG / 'fig_ablation.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved fig_ablation.png')


# ============ Fig 4: UAV (5 algos × 2 n_uavs, 3 metrics) ============
def plot_uav():
    data = load_uav()
    by_an = defaultdict(lambda: defaultdict(list))
    for r in data:
        if 'f1_value' in r:
            by_an[(r['algo'], r['n_uavs'])]['value'].append(r['f1_value'])
            by_an[(r['algo'], r['n_uavs'])]['time'].append(r['f2_response_time'])
            by_an[(r['algo'], r['n_uavs'])]['batt'].append(r['f3_battery'])
            by_an[(r['algo'], r['n_uavs'])]['inv'].append(r.get('invocations', 0))

    nuavs = sorted(set(r['n_uavs'] for r in data if 'n_uavs' in r))
    fig, axes = plt.subplots(2, 3, figsize=(15, 7))
    for ni, nu in enumerate(nuavs):
        for mi, (mkey, mlabel) in enumerate([('value', 'Task Value (↑)'),
                                              ('time', 'Response Time (↓)'),
                                              ('batt', 'Battery (↑)')]):
            ax = axes[ni, mi]
            for ai, algo in enumerate(ALGOS):
                d = by_an[(algo, nu)]
                if d['value']:
                    color = COLORS[ALGOS.index(algo)]
                    x_pos = ai
                    m = np.mean(d[mkey])
                    s = np.std(d[mkey])
                    ax.bar(x_pos, m, yerr=s, color=color, alpha=0.85, capsize=3, width=0.6)
                    ax.text(x_pos, m + s + 0.02 * max(1, abs(m)),
                            f'{m:.1f}', ha='center', fontsize=7)
            ax.set_xticks(range(len(ALGOS)))
            ax.set_xticklabels(ALGOS, rotation=20, ha='right', fontsize=8)
            ax.set_title(f'{mlabel} — n_uavs={nu}', fontsize=9)
            ax.grid(axis='y', alpha=0.3)
    fig.suptitle('Multi-UAV Task Allocation: 5 Algorithms × {4, 8} UAVs × 5 Seeds',
                 fontsize=12, y=1.01)
    plt.tight_layout()
    plt.savefig(FIG / 'fig_uav.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved fig_uav.png')


# ============ Fig 5: LLM invocations per algo (main DMO) ============
def plot_invocations():
    data = load_main()
    by_a = defaultdict(list)
    for r in data:
        if 'invocations' in r:
            by_a[r['algo']].append(r['invocations'])

    fig, ax = plt.subplots(figsize=(8, 4.5))
    means = [np.mean(by_a[a]) if by_a[a] else 0 for a in ALGOS]
    stds = [np.std(by_a[a]) if by_a[a] else 0 for a in ALGOS]
    x = np.arange(len(ALGOS))
    ax.bar(x, means, yerr=stds, color=COLORS, alpha=0.85, capsize=4)
    for i, (m, s) in enumerate(zip(means, stds)):
        ax.text(i, m + s + 0.5, f'{m:.1f}', ha='center', fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(ALGOS, rotation=15, ha='right', fontsize=9)
    ax.set_ylabel('Avg LLM Invocations per Run')
    ax.set_title('LLM Call Budget: TLE uses ~46 calls (5-15% of generations)')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIG / 'fig_llm_calls.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved fig_llm_calls.png')


# ============ Fig 6: Cost-quality tradeoff ============
def plot_cost_quality():
    data = load_main()
    by_a = defaultdict(lambda: {'inv': [], 'igd': []})
    for r in data:
        if 'invocations' in r and 'igd' in r and np.isfinite(r['igd']):
            by_a[r['algo']]['inv'].append(r['invocations'])
            by_a[r['algo']]['igd'].append(r['igd'])

    fig, ax = plt.subplots(figsize=(9, 5.5))
    for ai, algo in enumerate(ALGOS):
        d = by_a[algo]
        if d['inv']:
            x = np.mean(d['inv'])
            y = np.mean(d['igd'])
            s = 200 + 50 * ai
            ax.scatter(x, y, s=s, c=COLORS[ai], label=algo, alpha=0.85,
                       edgecolors='black', linewidth=1.5)
    ax.set_xlabel('Avg LLM Invocations per Run (cost)')
    ax.set_ylabel('Avg IGD across all problems (quality, lower=better)')
    ax.set_title('Cost vs. Quality: TLE achieves competitive quality at low LLM cost')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIG / 'fig_cost_quality.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved fig_cost_quality.png')


if __name__ == '__main__':
    plot_main_igd()
    plot_main_hv()
    plot_ablation()
    plot_uav()
    plot_invocations()
    plot_cost_quality()
    print('\nAll figures saved to', FIG)
