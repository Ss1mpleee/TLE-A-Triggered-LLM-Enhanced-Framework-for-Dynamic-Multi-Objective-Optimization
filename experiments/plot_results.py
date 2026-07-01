"""
Generate plots for the paper.
"""
import sys
sys.path.insert(0, "D:/新论文/实验")

import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict

RESULTS_DIR = Path("实验/results/raw").resolve()
FIG_DIR = Path("实验/results/figures").resolve()
FIG_DIR.mkdir(parents=True, exist_ok=True)


def load_results(filename):
    path = RESULTS_DIR / filename
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def plot_cec2018_bar(results, output="cec2018_igd.png"):
    """Bar chart of IGD per (algorithm, problem)."""
    by_ap = defaultdict(list)
    for r in results:
        if "error" in r or "igd" not in r:
            continue
        by_ap[(r["algo"], r["problem"])].append(r["igd"])

    problems = sorted(set(r["problem"] for r in results if "problem" in r))
    algos = ["DE", "DE-LM-random", "DE-LM-static-trigger", "TLE", "DE-LM-always"]

    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(problems))
    width = 0.16
    colors = ['#7f7f7f', '#bcbd22', '#17becf', '#d62728', '#9467bd']

    for i, algo in enumerate(algos):
        means = []
        stds = []
        for p in problems:
            vals = by_ap.get((algo, p), [])
            if vals:
                means.append(np.mean(vals))
                stds.append(np.std(vals))
            else:
                means.append(0)
                stds.append(0)
        ax.bar(x + (i - 2) * width, means, width, yerr=stds,
               label=algo, color=colors[i], alpha=0.85, capsize=3)

    ax.set_xticks(x)
    ax.set_xticklabels(problems)
    ax.set_ylabel("IGD (lower = better)")
    ax.set_xlabel("CEC2018 Problem")
    ax.set_title("IGD on CEC2018 Dynamic Multi-Objective Benchmarks")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIG_DIR / output, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {FIG_DIR / output}")


def plot_cec2018_hv(results, output="cec2018_hv.png"):
    """Bar chart of HV per (algorithm, problem)."""
    by_ap = defaultdict(list)
    for r in results:
        if "error" in r or "hv" not in r:
            continue
        by_ap[(r["algo"], r["problem"])].append(r["hv"])

    problems = sorted(set(r["problem"] for r in results if "problem" in r))
    algos = ["DE", "DE-LM-random", "DE-LM-static-trigger", "TLE", "DE-LM-always"]

    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(problems))
    width = 0.16
    colors = ['#7f7f7f', '#bcbd22', '#17becf', '#d62728', '#9467bd']

    for i, algo in enumerate(algos):
        means = []
        stds = []
        for p in problems:
            vals = by_ap.get((algo, p), [])
            if vals:
                means.append(np.mean(vals))
                stds.append(np.std(vals))
            else:
                means.append(0)
                stds.append(0)
        ax.bar(x + (i - 2) * width, means, width, yerr=stds,
               label=algo, color=colors[i], alpha=0.85, capsize=3)

    ax.set_xticks(x)
    ax.set_xticklabels(problems)
    ax.set_ylabel("HV (higher = better)")
    ax.set_xlabel("CEC2018 Problem")
    ax.set_title("Hypervolume on CEC2018 Dynamic Multi-Objective Benchmarks")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIG_DIR / output, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {FIG_DIR / output}")


def plot_uav_metrics(results, output="uav_metrics.png"):
    """3-bar chart of UAV value, time, battery."""
    by_algo = defaultdict(lambda: {"value": [], "time": [], "battery": []})
    for r in results:
        if "f1_value" in r:
            by_algo[r["algo"]]["value"].append(r["f1_value"])
            by_algo[r["algo"]]["time"].append(r["f2_response_time"])
            by_algo[r["algo"]]["battery"].append(r["f3_battery"])

    algos = list(by_algo.keys())
    metrics = ["value", "time", "battery"]
    titles = ["Total Task Value (higher = better)",
              "Avg Response Time (lower = better)",
              "Avg Battery Remaining (higher = better)"]
    colors = ['#d62728', '#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd']

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for i, (m, title) in enumerate(zip(metrics, titles)):
        means = [np.mean(by_algo[a][m]) if by_algo[a][m] else 0 for a in algos]
        stds = [np.std(by_algo[a][m]) if by_algo[a][m] else 0 for a in algos]
        x = np.arange(len(algos))
        axes[i].bar(x, means, yerr=stds, color=colors[:len(algos)],
                   alpha=0.85, capsize=4)
        axes[i].set_xticks(x)
        axes[i].set_xticklabels(algos, rotation=20, ha="right", fontsize=9)
        axes[i].set_title(title, fontsize=10)
        axes[i].grid(axis="y", alpha=0.3)
        # Annotate values
        for j, (mean, std) in enumerate(zip(means, stds)):
            axes[i].text(j, mean + std + 0.02 * (max(means) + 1),
                        f"{mean:.1f}", ha="center", fontsize=8)
    fig.suptitle("Multi-UAV Task Allocation: Comparison of 4 Algorithms (3 seeds, 4 UAVs)",
                fontsize=12, y=1.02)
    plt.tight_layout()
    plt.savefig(FIG_DIR / output, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {FIG_DIR / output}")


def plot_invocations(results, output="invocations.png"):
    """Bar chart of LLM invocations per algorithm."""
    by_algo = defaultdict(list)
    for r in results:
        if "invocations" in r:
            by_algo[r["algo"]].append(r["invocations"])

    algos = list(by_algo.keys())
    means = [np.mean(by_algo[a]) if by_algo[a] else 0 for a in algos]
    stds = [np.std(by_algo[a]) if by_algo[a] else 0 for a in algos]
    x = np.arange(len(algos))

    fig, ax = plt.subplots(figsize=(9, 4.5))
    colors = ['#7f7f7f', '#bcbd22', '#17becf', '#d62728', '#9467bd']
    bars = ax.bar(x, means, yerr=stds, color=colors[:len(algos)],
                  alpha=0.85, capsize=4)
    ax.set_xticks(x)
    ax.set_xticklabels(algos, rotation=15, ha="right", fontsize=10)
    ax.set_ylabel("LLM Invocations per Run (avg)")
    ax.set_title("LLM Call Budget Efficiency: TLE uses 1/3 the calls of DE-LM-always")
    ax.grid(axis="y", alpha=0.3)
    for j, mean in enumerate(means):
        ax.text(j, mean + max(means) * 0.02, f"{mean:.1f}",
                ha="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(FIG_DIR / output, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {FIG_DIR / output}")


def plot_convergence(results, output="convergence.png"):
    """Convergence curve (best fitness per gen) for TLE on DF1."""
    by_ap = defaultdict(lambda: defaultdict(list))
    for r in results:
        if "best_fitness_history" in r and r.get("best_fitness_history"):
            for i, v in enumerate(r["best_fitness_history"]):
                by_ap[r["algo"]][i].append(v)

    algos_to_plot = ["DE", "DE-LM-static-trigger", "TLE", "DE-LM-always"]
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ['#7f7f7f', '#17becf', '#d62728', '#9467bd']

    for algo, color in zip(algos_to_plot, colors):
        if algo not in by_ap:
            continue
        gens = sorted(by_ap[algo].keys())
        means = [np.mean(by_ap[algo][g]) for g in gens]
        stds = [np.std(by_ap[algo][g]) for g in gens]
        ax.plot(gens, means, label=algo, color=color, linewidth=1.5)
        ax.fill_between(gens,
                        [m - s for m, s in zip(means, stds)],
                        [m + s for m, s in zip(means, stds)],
                        alpha=0.15, color=color)

    ax.set_xlabel("Generation")
    ax.set_ylabel("Sum of Objectives (lower = better)")
    ax.set_title("Convergence on CEC2018 DF1 (3 seeds, mean ± std)")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIG_DIR / output, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {FIG_DIR / output}")


if __name__ == "__main__":
    # Load results
    cec2018 = load_results("exp2_dynamic_mo.json")
    uav = load_results("exp3_uav.json")

    if cec2018:
        print(f"Loaded {len(cec2018)} CEC2018 results")
        plot_cec2018_bar(cec2018)
        plot_cec2018_hv(cec2018)
        plot_convergence(cec2018)
    if uav:
        print(f"Loaded {len(uav)} UAV results")
        plot_uav_metrics(uav)
        plot_invocations(uav)

    print("\nAll plots saved to:", FIG_DIR)
