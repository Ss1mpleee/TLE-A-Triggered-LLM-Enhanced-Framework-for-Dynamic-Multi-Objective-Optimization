"""
Statistical analysis: Wilcoxon signed-rank test + generate final plots.
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
from scipy import stats

RESULTS_DIR = Path("实验/results/raw")
FIG_DIR = Path("实验/results/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)


# Load all results
def load(path):
    full = RESULTS_DIR / path
    if not full.exists():
        return []
    with open(full, "r", encoding="utf-8") as f:
        return json.load(f)

main_data = load("sec_main.json")
ablation_data = load("sec_ablation.json")


# ============ Wilcoxon Signed-Rank Test ============
print("=" * 80)
print("WILCOXON SIGNED-RANK TEST (TLE vs Baselines)")
print("=" * 80)

def group(data, key):
    out = defaultdict(list)
    for r in data:
        if "error" in r or "igd" not in r:
            continue
        out[r[key]].append(r["igd"])
    return out

main_by_ap = group(main_data, "problem")
main_by_algo_problem = defaultdict(dict)
for r in main_data:
    if "error" in r or "igd" not in r:
        continue
    main_by_algo_problem[r["problem"]][r["algo"]] = r["igd"]

print(f"\n{'Problem':10s} | {'Baseline':20s} | {'TLE mean':10s} | {'Baseline mean':13s} | "
      f"{'p-value':10s} | {'Significant':12s}")
print("-" * 100)
for prob, algos_dict in main_by_algo_problem.items():
    if "TLE" not in algos_dict:
        continue
    tle_vals = [algos_dict[a] for a, v in [
        ("DE", 0), ("DE-LM-static-trigger", 0), ("PPS-DMOEA", 0)
    ] if a in algos_dict]
    # Get all baseline IGDs
    for baseline in ["DE", "DE-LM-static-trigger", "PPS-DMOEA"]:
        if baseline not in algos_dict:
            continue
        # Align by seed
        tle_per_seed = {}
        base_per_seed = {}
        for r in main_data:
            if r["problem"] != prob:
                continue
            if r["algo"] == "TLE":
                tle_per_seed[r["seed"]] = r["igd"]
            elif r["algo"] == baseline:
                base_per_seed[r["seed"]] = r["igd"]
        common_seeds = sorted(set(tle_per_seed) & set(base_per_seed))
        if len(common_seeds) < 3:
            continue
        tle_arr = [tle_per_seed[s] for s in common_seeds]
        base_arr = [base_per_seed[s] for s in common_seeds]
        try:
            stat, p = stats.wilcoxon(tle_arr, base_arr, alternative="less")
        except Exception:
            stat, p = 0.0, 1.0
        sig = "YES" if p < 0.05 else "no"
        tle_mean = np.mean(tle_arr)
        base_mean = np.mean(base_arr)
        print(f"{prob:10s} | {baseline:20s} | {tle_mean:.4f}     | {base_mean:.4f}        | "
              f"{p:.4f}    | {sig}")

# Save to file
sig_results = {}
for prob, algos_dict in main_by_algo_problem.items():
    if "TLE" not in algos_dict:
        continue
    sig_results[prob] = {}
    for baseline in ["DE", "DE-LM-static-trigger", "PPS-DMOEA"]:
        if baseline not in algos_dict:
            continue
        tle_per_seed = {}
        base_per_seed = {}
        for r in main_data:
            if r["problem"] != prob:
                continue
            if r["algo"] == "TLE":
                tle_per_seed[r["seed"]] = r["igd"]
            elif r["algo"] == baseline:
                base_per_seed[r["seed"]] = r["igd"]
        common_seeds = sorted(set(tle_per_seed) & set(base_per_seed))
        if len(common_seeds) < 3:
            continue
        tle_arr = [tle_per_seed[s] for s in common_seeds]
        base_arr = [base_per_seed[s] for s in common_seeds]
        try:
            stat, p = stats.wilcoxon(tle_arr, base_arr, alternative="less")
        except Exception:
            stat, p = 0.0, 1.0
        sig_results[prob][baseline] = {
            "p_value": float(p),
            "TLE_mean": float(np.mean(tle_arr)),
            "TLE_std": float(np.std(tle_arr)),
            "baseline_mean": float(np.mean(base_arr)),
            "baseline_std": float(np.std(base_arr)),
            "significant": p < 0.05,
            "n_seeds": len(common_seeds),
        }

with open(RESULTS_DIR / "wilcoxon_results.json", "w", encoding="utf-8") as f:
    json.dump(sig_results, f, ensure_ascii=False, indent=2)
print(f"\nSaved: {RESULTS_DIR / 'wilcoxon_results.json'}")


# ============ Summary Table ============
print("\n" + "=" * 80)
print("SUMMARY TABLE: IGD on CEC2018 Dynamic Benchmarks (5 seeds, mean ± std)")
print("=" * 80)

algos = ["DE", "DE-LM-static-trigger", "PPS-DMOEA", "TLE"]
problems = ["DF1", "DF5"]
for prob in problems:
    print(f"\n{prob}:")
    print(f"  {'Algorithm':25s} | {'IGD (mean ± std)':25s} | {'Invocations (mean)':18s}")
    print("  " + "-" * 75)
    for algo in algos:
        vals = [r["igd"] for r in main_data
                if r.get("problem") == prob and r.get("algo") == algo and "error" not in r]
        invs = [r.get("invocations", 0) for r in main_data
                if r.get("problem") == prob and r.get("algo") == algo and "error" not in r]
        if vals:
            sig_str = "***" if sig_results.get(prob, {}).get(algo, {}).get("significant") else ""
            print(f"  {algo:25s} | {np.mean(vals):.4f} ± {np.std(vals):.4f}{sig_str:10s}  | {np.mean(invs):.1f}")


# ============ Ablation Results ============
print("\n" + "=" * 80)
print("ABLATION STUDY (3 seeds, max_gen=200)")
print("=" * 80)

ablation_by_vp = defaultdict(list)
for r in ablation_data:
    if "error" in r:
        continue
    ablation_by_vp[(r["variant"], r["problem"])].append(r["igd"])

variants_order = ["V3_no_llm", "V2_heuristic_budget", "V1_single_signal", "V0_TLE_full"]
variant_names = {
    "V3_no_llm": "V3: Pure DE (no LLM)",
    "V2_heuristic_budget": "V2: TLE + heuristic budget",
    "V1_single_signal": "V1: TLE + single signal",
    "V0_TLE_full": "V0: Full TLE (our method)",
}

for prob in problems:
    print(f"\n{prob}:")
    for v in variants_order:
        vals = ablation_by_vp.get((v, prob), [])
        if vals:
            print(f"  {variant_names[v]:35s} | IGD: {np.mean(vals):.4f} ± {np.std(vals):.4f}")


# ============ Plot 1: Final IGD comparison ============
fig, ax = plt.subplots(figsize=(11, 5.5))
x = np.arange(len(problems))
width = 0.18
colors = ['#7f7f7f', '#17becf', '#9467bd', '#d62728']

for i, algo in enumerate(algos):
    means = []
    stds = []
    for p in problems:
        vals = [r["igd"] for r in main_data
                if r.get("problem") == p and r.get("algo") == algo and "error" not in r]
        if vals:
            means.append(np.mean(vals))
            stds.append(np.std(vals))
        else:
            means.append(0)
            stds.append(0)
    bars = ax.bar(x + (i - 1.5) * width, means, width, yerr=stds,
                  label=algo, color=colors[i], alpha=0.85, capsize=3)

# Annotate significance
for i_p, p in enumerate(problems):
    for i_a, algo in enumerate(algos):
        if algo == "TLE":
            continue
        sig = sig_results.get(p, {}).get(algo, {})
        if sig.get("significant"):
            x_pos = i_p + (i_a - 1.5) * width
            tle_x = i_p + (algos.index("TLE") - 1.5) * width
            ax.plot([x_pos, tle_x], [0.005, 0.005], 'k-', linewidth=0.8, alpha=0.5)
            ax.text((x_pos + tle_x) / 2, 0.0055, "*", ha="center", fontsize=12, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(problems)
ax.set_ylabel("IGD (lower = better)")
ax.set_xlabel("CEC2018 Problem")
ax.set_title("Main Comparison: TLE vs 3 Baselines (5 seeds, max_gen=200, * = p<0.05)")
ax.legend(loc="upper left", fontsize=10)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(FIG_DIR / "fig_main_comparison.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"\nSaved: {FIG_DIR / 'fig_main_comparison.png'}")


# ============ Plot 2: Ablation ============
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
for i_p, prob in enumerate(problems):
    ax = axes[i_p]
    means = []
    stds = []
    labels = []
    for v in variants_order:
        vals = ablation_by_vp.get((v, prob), [])
        if vals:
            means.append(np.mean(vals))
            stds.append(np.std(vals))
            labels.append(v.replace("_", "\n"))
    x = np.arange(len(labels))
    colors_ab = ['#7f7f7f', '#bcbd22', '#17becf', '#d62728']
    ax.bar(x, means, yerr=stds, color=colors_ab, alpha=0.85, capsize=4)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("IGD")
    ax.set_title(f"{prob}")
    ax.grid(axis="y", alpha=0.3)
    # Highlight V0
    if i_p == 0:
        for j, (m, s) in enumerate(zip(means, stds)):
            ax.text(j, m + s + 0.002, f"{m:.4f}", ha="center", fontsize=9)

fig.suptitle("Ablation Study: TLE Components Contribution (3 seeds, max_gen=200)", y=1.02)
plt.tight_layout()
plt.savefig(FIG_DIR / "fig_ablation.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {FIG_DIR / 'fig_ablation.png'}")


# ============ Plot 3: Convergence on DF5 ============
fig, ax = plt.subplots(figsize=(10, 5))
# Get best_fitness_history for first seed of each algo
colors = {'DE': '#7f7f7f', 'DE-LM-static-trigger': '#17becf', 'PPS-DMOEA': '#9467bd', 'TLE': '#d62728'}
for algo in algos:
    for r in main_data:
        if r.get("problem") == "DF5" and r.get("algo") == algo and r.get("seed") == 0:
            if "best_fitness_history" in r and r["best_fitness_history"]:
                gens = range(len(r["best_fitness_history"]))
                ax.plot(gens, r["best_fitness_history"], label=algo, color=colors[algo], linewidth=1.8)
            break
ax.set_xlabel("Generation")
ax.set_ylabel("Sum of Objectives (lower = better)")
ax.set_title("Convergence on DF5 (seed=0, max_gen=200)")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(FIG_DIR / "fig_convergence.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {FIG_DIR / 'fig_convergence.png'}")


# ============ Plot 4: LLM invocations vs IGD ============
fig, ax = plt.subplots(figsize=(9, 5.5))
algos_4 = ["DE", "DE-LM-static-trigger", "PPS-DMOEA", "TLE"]
for algo in algos_4:
    invs = []
    igds = []
    for p in problems:
        for r in main_data:
            if r.get("problem") == p and r.get("algo") == algo and "error" not in r:
                invs.append(r.get("invocations", 0))
                igds.append(r["igd"])
    if invs:
        ax.scatter(np.mean(invs), np.mean(igds), s=200, alpha=0.85,
                   color=colors[algo], label=algo, edgecolors='black', linewidth=1.5)
ax.set_xlabel("Avg LLM Invocations per Run")
ax.set_ylabel("Avg IGD (lower = better)")
ax.set_title("Cost vs Quality Tradeoff")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(FIG_DIR / "fig_cost_quality.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {FIG_DIR / 'fig_cost_quality.png'}")

print("\nAll analysis complete!")
