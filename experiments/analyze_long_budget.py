"""
Analyze long-budget experiment and generate plots.
"""
import sys
sys.path.insert(0, "D:/新论文/实验")

import json
import numpy as np
from pathlib import Path
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS_DIR = Path("实验/results/raw")
FIG_DIR = Path("实验/results/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Load long-budget results
with open(RESULTS_DIR / "exp_long_budget.json", "r", encoding="utf-8") as f:
    results = json.load(f)

# Load short-budget for comparison
with open(RESULTS_DIR / "exp2_dynamic_mo.json", "r", encoding="utf-8") as f:
    short_results = json.load(f)

# Group by (algo, problem, budget)
def group_by_3way(data, max_gen_filter=None):
    out = defaultdict(list)
    for r in data:
        if "error" in r or "igd_final" not in r:
            continue
        if max_gen_filter is not None and r.get("max_gen") != max_gen_filter:
            continue
        out[(r["algo"], r["problem"])].append((r["igd_final"], r["invocations"]))
    return out

long_data = group_by_3way(results, max_gen_filter=200)

# Group short-budget
short_by_ap = defaultdict(list)
for r in short_results:
    if "error" in r or "igd" not in r:
        continue
    short_by_ap[(r["algo"], r["problem"])].append((r["igd"], r["invocations"]))

# ============ Plot 1: IGD comparison long vs short ============
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

algos = ["DE", "DE-LM-static-trigger", "TLE"]
problems = ["DF1", "DF5"]
colors = ['#7f7f7f', '#17becf', '#d62728']

for prob_idx, prob in enumerate(problems):
    ax = axes[prob_idx]
    x = np.arange(len(algos))
    width = 0.35

    # Short budget
    short_means = []
    short_stds = []
    for algo in algos:
        vals = short_by_ap.get((algo, prob), [])
        if vals:
            short_means.append(np.mean([v[0] for v in vals]))
            short_stds.append(np.std([v[0] for v in vals]))
        else:
            short_means.append(0)
            short_stds.append(0)
    # Long budget
    long_means = []
    long_stds = []
    for algo in algos:
        vals = long_data.get((algo, prob), [])
        if vals:
            long_means.append(np.mean([v[0] for v in vals]))
            long_stds.append(np.std([v[0] for v in vals]))
        else:
            long_means.append(0)
            long_stds.append(0)

    ax.bar(x - width/2, short_means, width, yerr=short_stds,
           label="Short (max_gen=60)", color='#bcbd22', alpha=0.85, capsize=3)
    ax.bar(x + width/2, long_means, width, yerr=long_stds,
           label="Long (max_gen=200)", color='#d62728', alpha=0.85, capsize=3)

    ax.set_xticks(x)
    ax.set_xticklabels(algos, rotation=15)
    ax.set_ylabel("IGD (lower = better)")
    ax.set_title(f"{prob}")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    # Annotate TLE improvement
    tle_idx = algos.index("TLE")
    if long_means[tle_idx] > 0 and short_means[tle_idx] > 0:
        improvement = (short_means[tle_idx] - long_means[tle_idx]) / short_means[tle_idx] * 100
        ax.annotate(f"TLE long: {long_means[tle_idx]:.4f}",
                    xy=(tle_idx + width/2, long_means[tle_idx] + long_stds[tle_idx] + 0.002),
                    ha="center", fontsize=9, color='#d62728', fontweight='bold')

fig.suptitle("Long-Budget Validation: TLE's Advantage Emerges at max_gen=200", y=1.02)
plt.tight_layout()
plt.savefig(FIG_DIR / "long_budget_validation.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {FIG_DIR / 'long_budget_validation.png'}")

# ============ Plot 2: LLM calls comparison ============
fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(len(algos))
width = 0.35

# Short
short_invs = [np.mean([v[1] for v in short_by_ap.get((a, "DF5"), [])]) for a in algos]
short_invs_stds = [np.std([v[1] for v in short_by_ap.get((a, "DF5"), [])]) for a in algos]
# Long
long_invs = [np.mean([v[1] for v in long_data.get((a, "DF5"), [])]) for a in algos]
long_invs_stds = [np.std([v[1] for v in long_data.get((a, "DF5"), [])]) for a in algos]

ax.bar(x - width/2, short_invs, width, yerr=short_invs_stds,
       label="Short (max_gen=60)", color='#bcbd22', alpha=0.85, capsize=3)
ax.bar(x + width/2, long_invs, width, yerr=long_invs_stds,
       label="Long (max_gen=200)", color='#3b82f6', alpha=0.85, capsize=3)

ax.set_xticks(x)
ax.set_xticklabels(algos)
ax.set_ylabel("LLM Invocations per Run")
ax.set_title("LLM Call Budget Usage: TLE Stays Low Even at Long Budget")
ax.legend()
ax.grid(axis="y", alpha=0.3)
for i, (s, l) in enumerate(zip(short_invs, long_invs)):
    ax.text(i - width/2, s + 1, f"{s:.0f}", ha="center", fontsize=9)
    ax.text(i + width/2, l + 1, f"{l:.0f}", ha="center", fontsize=9)

plt.tight_layout()
plt.savefig(FIG_DIR / "llm_calls_long_vs_short.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {FIG_DIR / 'llm_calls_long_vs_short.png'}")

# ============ Print detailed analysis ============
print("\n" + "=" * 70)
print("LONG-BUDGET ANALYSIS (max_gen=200)")
print("=" * 70)
print()
print("TLE's advantage: it's self-adaptive, so it learns to call LLM only when needed.")
print("DE-LM-static uses fixed exponential decay, which over-allocates at long budgets.")
print()

for prob in problems:
    print(f"\n--- Problem: {prob} ---")
    print(f"{'Algorithm':25s} | {'Short (60)':15s} | {'Long (200)':15s} | "
          f"{'Change':10s} | {'Invocations (200)':20s}")
    print("-" * 100)
    for algo in algos:
        s_vals = short_by_ap.get((algo, prob), [])
        l_vals = long_data.get((algo, prob), [])
        s_igd = np.mean([v[0] for v in s_vals]) if s_vals else 0
        l_igd = np.mean([v[0] for v in l_vals]) if l_vals else 0
        l_invs = [v[1] for v in l_vals]
        l_inv_mean = np.mean(l_invs) if l_invs else 0
        change = (s_igd - l_igd) / s_igd * 100 if s_igd > 0 else 0
        s_str = f"{s_igd:.4f} ± {np.std([v[0] for v in s_vals]):.4f}" if s_vals else "N/A"
        l_str = f"{l_igd:.4f} ± {np.std([v[0] for v in l_vals]):.4f}" if l_vals else "N/A"
        inv_str = f"{l_inv_mean:.1f} ± {np.std(l_invs):.1f}" if l_invs else "N/A"
        print(f"{algo:25s} | {s_str:15s} | {l_str:15s} | {change:+8.1f}%  | {inv_str:20s}")

# Key finding
print("\n" + "=" * 70)
print("KEY FINDING")
print("=" * 70)

for prob in problems:
    tle_l = [v[0] for v in long_data.get(("TLE", prob), [])]
    de_l = [v[0] for v in long_data.get(("DE", prob), [])]
    static_l = [v[0] for v in long_data.get(("DE-LM-static-trigger", prob), [])]

    if tle_l and de_l and static_l:
        tle_mean = np.mean(tle_l)
        de_mean = np.mean(de_l)
        static_mean = np.mean(static_l)

        print(f"\n{prob}:")
        print(f"  TLE = {tle_mean:.4f}")
        print(f"  DE  = {de_mean:.4f}  (TLE is {(de_mean-tle_mean)/de_mean*100:+.1f}% {'better' if tle_mean < de_mean else 'worse'})")
        print(f"  Static = {static_mean:.4f}  (TLE is {(static_mean-tle_mean)/static_mean*100:+.1f}% {'better' if tle_mean < static_mean else 'worse'})")
