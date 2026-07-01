"""
Final analysis with sec_main_v2.json (fixed PPS).
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

# Load results
def load(path):
    full = RESULTS_DIR / path
    if not full.exists():
        return []
    with open(full, "r", encoding="utf-8") as f:
        return json.load(f)

main_data = load("sec_main_v2.json")
ablation_data = load("sec_ablation.json")

# Group
def group_by_ap(data, key="algo"):
    out = defaultdict(dict)
    for r in data:
        if "error" in r or "igd" not in r:
            continue
        algo = r.get(key) or r.get("variant")
        out[r["problem"]][algo] = r["igd"]
    return out

main_by_ap = group_by_ap(main_data)
ablation_by_vp = defaultdict(list)
for r in ablation_data:
    if "error" in r:
        continue
    ablation_by_vp[(r["variant"], r["problem"])].append(r["igd"])


# ============ Wilcoxon + Summary ============
print("=" * 80)
print("FINAL SUMMARY: 4 Algorithms × 2 Problems × 5 Seeds (max_gen=200)")
print("=" * 80)

problems = ["DF1", "DF5"]
algos = ["DE", "DE-LM-static-trigger", "PPS-DMOEA", "TLE"]

print(f"\n{'Problem':10s} | {'Algorithm':22s} | {'IGD (mean ± std)':25s} | {'Invocations':12s}")
print("-" * 90)

results_table = []
for prob in problems:
    for algo in algos:
        vals = []
        invs = []
        for r in main_data:
            if r["problem"] == prob and r["algo"] == algo and "error" not in r:
                vals.append(r["igd"])
                invs.append(r.get("invocations", 0))
        if vals:
            mean_v = np.mean(vals)
            std_v = np.std(vals)
            mean_inv = np.mean(invs)
            print(f"{prob:10s} | {algo:22s} | {mean_v:.4f} ± {std_v:.4f}        | {mean_inv:.1f}")
            results_table.append({
                "problem": prob, "algo": algo,
                "igd_mean": mean_v, "igd_std": std_v,
                "invocations": mean_inv,
            })
    print()


# ============ Wilcoxon Test ============
print("\n=== Wilcoxon Signed-Rank Test (TLE vs Baselines) ===")
print(f"{'Problem':10s} | {'Baseline':22s} | {'TLE mean':10s} | {'Base mean':10s} | {'p-value':10s} | {'Sig':10s}")
print("-" * 90)
sig_results = {}
for prob in problems:
    sig_results[prob] = {}
    for baseline in algos:
        if baseline == "TLE":
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
        common = sorted(set(tle_per_seed) & set(base_per_seed))
        if len(common) < 3:
            continue
        tle_arr = [tle_per_seed[s] for s in common]
        base_arr = [base_per_seed[s] for s in common]
        try:
            stat, p = stats.wilcoxon(tle_arr, base_arr, alternative="less")
        except Exception:
            p = 1.0
        sig = "YES" if p < 0.05 else ("~" if p < 0.1 else "no")
        tle_mean = np.mean(tle_arr)
        base_mean = np.mean(base_arr)
        print(f"{prob:10s} | {baseline:22s} | {tle_mean:.4f}     | {base_mean:.4f}    | {p:.4f}     | {sig}")
        sig_results[prob][baseline] = {
            "p_value": float(p),
            "TLE_mean": float(tle_mean),
            "baseline_mean": float(base_mean),
            "improvement_pct": float((base_mean - tle_mean) / base_mean * 100),
            "significant": p < 0.05,
            "n_seeds": len(common),
        }

with open(RESULTS_DIR / "wilcoxon_results.json", "w", encoding="utf-8") as f:
    json.dump(sig_results, f, ensure_ascii=False, indent=2)


# ============ Ablation ============
print("\n" + "=" * 80)
print("ABLATION STUDY: 4 Variants × 2 Problems × 3 Seeds (max_gen=200)")
print("=" * 80)

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
            mean_v = np.mean(vals)
            std_v = np.std(vals)
            print(f"  {variant_names[v]:40s} | IGD: {mean_v:.4f} ± {std_v:.4f}")


# ============ Final Figure 1: Main Comparison Bar Chart ============
fig, ax = plt.subplots(figsize=(11, 5.5))
x = np.arange(len(problems))
width = 0.18
colors = ['#7f7f7f', '#17becf', '#9467bd', '#d62728']

for i, algo in enumerate(algos):
    means = []
    stds = []
    for p in problems:
        vals = []
        for r in main_data:
            if r.get("problem") == p and r.get("algo") == algo and "error" not in r:
                vals.append(r["igd"])
        if vals:
            means.append(np.mean(vals))
            stds.append(np.std(vals))
        else:
            means.append(0)
            stds.append(0)
    ax.bar(x + (i - 1.5) * width, means, width, yerr=stds,
           label=algo, color=colors[i], alpha=0.85, capsize=3)

# Significance bars
for i_p, p in enumerate(problems):
    for i_a, algo in enumerate(algos):
        if algo == "TLE":
            continue
        sig = sig_results.get(p, {}).get(algo, {})
        if sig.get("p_value", 1.0) < 0.1:
            x_pos = i_p + (i_a - 1.5) * width
            tle_x = i_p + (algos.index("TLE") - 1.5) * width
            y_pos = max(means) * 1.15
            ax.plot([x_pos, tle_x], [y_pos, y_pos], 'k-', linewidth=0.8, alpha=0.5)
            sym = "***" if sig.get("p_value", 1.0) < 0.01 else ("*" if sig.get("p_value", 1.0) < 0.05 else "~")
            ax.text((x_pos + tle_x) / 2, y_pos + 0.005, sym, ha="center", fontsize=11, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(problems)
ax.set_ylabel("IGD (lower = better)")
ax.set_xlabel("CEC2018 Problem")
ax.set_title("Main Comparison (5 seeds, max_gen=200): TLE vs 3 Baselines")
ax.legend(loc="upper left", fontsize=10)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(FIG_DIR / "fig_main_comparison.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"\nSaved: {FIG_DIR / 'fig_main_comparison.png'}")


# ============ Figure 2: Ablation ============
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
    bars = ax.bar(x, means, yerr=stds, color=colors_ab, alpha=0.85, capsize=4)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("IGD")
    ax.set_title(f"Ablation: {prob}")
    ax.grid(axis="y", alpha=0.3)
    for j, (m, s) in enumerate(zip(means, stds)):
        ax.text(j, m + s + 0.001, f"{m:.4f}", ha="center", fontsize=9)

fig.suptitle("Ablation Study: Each Component's Contribution (3 seeds, max_gen=200)", y=1.02)
plt.tight_layout()
plt.savefig(FIG_DIR / "fig_ablation.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {FIG_DIR / 'fig_ablation.png'}")


# ============ Figure 3: Convergence on DF5 ============
fig, ax = plt.subplots(figsize=(10, 5))
colors = {'DE': '#7f7f7f', 'DE-LM-static-trigger': '#17becf', 'PPS-DMOEA': '#9467bd', 'TLE': '#d62728'}
for algo in algos:
    for r in main_data:
        if r.get("problem") == "DF5" and r.get("algo") == algo and r.get("seed") == 0:
            if "best_fitness_history" in r and r["best_fitness_history"]:
                gens = range(len(r["best_fitness_history"]))
                # Smooth
                h = r["best_fitness_history"]
                ax.plot(gens, h, label=algo, color=colors[algo], linewidth=1.8, alpha=0.85)
            break
ax.set_xlabel("Generation")
ax.set_ylabel("Sum of Objectives (lower = better)")
ax.set_title("Convergence on DF5 (seed=0, max_gen=200)")
ax.legend()
ax.grid(alpha=0.3)
ax.set_yscale("log")
plt.tight_layout()
plt.savefig(FIG_DIR / "fig_convergence.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {FIG_DIR / 'fig_convergence.png'}")


# ============ Figure 4: LLM Cost vs Quality Pareto ============
fig, ax = plt.subplots(figsize=(9, 5.5))
for algo in algos:
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
ax.set_title("Cost vs Quality Tradeoff (TLE balances both)")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(FIG_DIR / "fig_cost_quality.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {FIG_DIR / 'fig_cost_quality.png'}")


# ============ Figure 5: LLM Calls Detail ============
fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(len(algos))
width = 0.35
short_invs = []
short_invs_std = []
long_invs = []
long_invs_std = []
# Use max_gen=200 (long) and short if available
for algo in algos:
    s_invs = []
    l_invs = []
    for p in problems:
        for r in main_data:
            if r["problem"] == p and r["algo"] == algo and "error" not in r:
                # max_gen=200 is our current data
                l_invs.append(r.get("invocations", 0))
    long_invs.append(np.mean(l_invs) if l_invs else 0)
    long_invs_std.append(np.std(l_invs) if l_invs else 0)
    short_invs.append(0)
    short_invs_std.append(0)

ax.bar(x, long_invs, yerr=long_invs_std, color=colors, alpha=0.85, capsize=4)
ax.set_xticks(x)
ax.set_xticklabels(algos)
ax.set_ylabel("Avg LLM Invocations per Run (max_gen=200)")
ax.set_title("LLM Call Budget Usage (Long-Budget: 5 seeds × 2 problems avg)")
ax.grid(axis="y", alpha=0.3)
for i, (v, s) in enumerate(zip(long_invs, long_invs_std)):
    ax.text(i, v + s + 1, f"{v:.1f}", ha="center", fontsize=10)
plt.tight_layout()
plt.savefig(FIG_DIR / "fig_llm_calls.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {FIG_DIR / 'fig_llm_calls.png'}")

# Save results table
with open(RESULTS_DIR / "summary_table.md", "w", encoding="utf-8") as f:
    f.write("# Summary Table: IGD on CEC2018 Dynamic Benchmarks\n\n")
    f.write("5 seeds, max_gen=200, pop_size=50, 10 dimensions\n\n")
    f.write("| Problem | Algorithm | IGD (mean ± std) | LLM Calls |\n")
    f.write("|---|---|---|---|\n")
    for r in results_table:
        f.write(f"| {r['problem']} | {r['algo']} | {r['igd_mean']:.4f} ± {r['igd_std']:.4f} | {r['invocations']:.1f} |\n")
    f.write("\n## Wilcoxon Test (TLE vs Baselines)\n\n")
    for prob in problems:
        f.write(f"### {prob}\n\n")
        f.write("| Baseline | TLE mean | Baseline mean | p-value | Significant |\n")
        f.write("|---|---|---|---|---|\n")
        for baseline in algos:
            if baseline == "TLE":
                continue
            sig = sig_results.get(prob, {}).get(baseline, {})
            if sig:
                sig_marker = "***" if sig.get("p_value", 1) < 0.01 else ("*" if sig.get("p_value", 1) < 0.05 else ("~" if sig.get("p_value", 1) < 0.1 else "no"))
                f.write(f"| {baseline} | {sig.get('TLE_mean', 0):.4f} | {sig.get('baseline_mean', 0):.4f} | "
                        f"{sig.get('p_value', 1):.4f} | {sig_marker} ({sig.get('improvement_pct', 0):+.1f}%) |\n")
        f.write("\n")

print(f"\nSaved summary: {RESULTS_DIR / 'summary_table.md'}")
print("\nAll analysis complete!")
