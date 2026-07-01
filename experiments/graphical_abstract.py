"""
graphical_abstract.py
Generate a 5x5 cm graphical abstract for the TLE paper (Swarm and Evolutionary Computation).

Print: 5 x 5 cm @ 600 dpi = 1181 x 1181 px. Figure 1.97 x 1.97 inches.

Layout: vertical 4-tier flow diagram.
  Tier 1: Title
  Tier 2: 3 trigger signals (3 columns)
  Tier 3: TLE Framework (1 outer + 3 sub-modules + 1 base)
  Tier 4: Outcomes (theory + empirical)

To avoid text overflow, this version:
  - uses very small font sizes (3-4 pt for box labels)
  - uses short, single-word labels where possible
  - uses TIGHT boxes (no wasted whitespace)
  - places outcome labels OUTSIDE the boxes (under each box)
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path


HERE = Path(__file__).resolve().parent
FIG_DIR = HERE.parents[1] / "论文" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


# Color palette
C_TRIGGER = "#E76F51"
C_LLM     = "#2A9D8F"
C_BANDIT  = "#264653"
C_DE      = "#F4A261"
C_THEORY  = "#6A4C93"
C_RESULT  = "#8AB17D"
C_TEXT    = "#222831"


def box(ax, x, y, w, h, color, text="", fs=4, fontweight="normal",
        textcolor="white", alpha=1.0, zorder=3, radius=0.01):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.002,rounding_size={radius}",
        linewidth=0, edgecolor=color, facecolor=color,
        alpha=alpha, zorder=zorder,
    ))
    if text:
        ax.text(x + w / 2, y + h / 2, text,
                ha="center", va="center", fontsize=fs, color=textcolor,
                fontweight=fontweight, zorder=zorder + 1)


def arrow(ax, start, end, color="#777", lw=0.6, style="-|>", mutation=6):
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle=style, color=color, lw=lw,
        mutation_scale=mutation, zorder=2,
    ))


def main():
    side_in = 5.0 / 2.54
    fig = plt.figure(figsize=(side_in, side_in), dpi=600)
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # ===== Tier 1: TITLE =====
    ax.text(0.5, 0.96, "TLE:  Triggered LLM-Enhanced EA",
            ha="center", va="center", fontsize=5.2, fontweight="bold", color=C_TEXT)
    ax.text(0.5, 0.92, "for Dynamic Multi-Objective Optimization",
            ha="center", va="center", fontsize=4.2, color="#555", style="italic")

    # ===== Tier 2: THREE TRIGGER SIGNALS =====
    tri_y, tri_h = 0.80, 0.07
    tri_w = 0.30
    gap = 0.015
    x0 = (1 - (3 * tri_w + 2 * gap)) / 2
    triggers = ["Population\nentropy", "Fitness\nstagnation", "Environmental\nchange"]
    for i, label in enumerate(triggers):
        x = x0 + i * (tri_w + gap)
        box(ax, x, tri_y, tri_w, tri_h, C_TRIGGER,
            text=label, fs=4, fontweight="bold", textcolor="white", radius=0.012)
    # arrows down
    for i in range(3):
        x_arrow = x0 + i * (tri_w + gap) + tri_w / 2
        arrow(ax, (x_arrow, tri_y), (0.5, 0.72),
              color=C_TRIGGER, lw=0.6, mutation=5)

    # ===== Tier 3: TLE FRAMEWORK =====
    core_x, core_y, core_w, core_h = 0.05, 0.46, 0.90, 0.24
    box(ax, core_x, core_y, core_w, core_h, C_LLM,
        text="", textcolor="white", radius=0.012, alpha=0.92)

    # TLE label at top of the core
    ax.text(core_x + core_w / 2, core_y + core_h - 0.022, "TLE Framework",
            ha="center", va="center", fontsize=5.5, fontweight="bold", color="white")

    # 3 sub-modules horizontally
    sub_y = core_y + 0.085
    sub_h = 0.075
    sub_w = 0.28
    sub_gap = 0.013
    sub_x0 = core_x + 0.015
    sub_modules = [
        ("Trigger", C_TRIGGER),
        ("Mapping", C_LLM),
        ("Bandit",  C_BANDIT),
    ]
    for i, (label, color) in enumerate(sub_modules):
        x = sub_x0 + i * (sub_w + sub_gap)
        box(ax, x, sub_y, sub_w, sub_h, color,
            text=label, fs=4.5, fontweight="bold", textcolor="white",
            alpha=0.97, radius=0.008)

    # (No sub-labels — keep figure clean; the colors and module names
    #  already differentiate Trigger / Mapping / Bandit.)

    # 1 base DE pill below
    base_y = core_y + 0.018
    base_w = 0.55
    base_x = core_x + (core_w - base_w) / 2
    box(ax, base_x, base_y, base_w, 0.045, C_DE,
        text="DE/rand/1/bin  +  NSGA-II",
        fs=4, fontweight="bold", textcolor="white", alpha=0.97, radius=0.008)

    # arrow down from TLE to outcomes
    arrow(ax, (0.5, core_y - 0.005), (0.5, 0.42),
          color=C_BANDIT, lw=0.7, mutation=6)

    # ===== Tier 4: TWO OUTCOME BOXES =====
    out_y, out_h = 0.22, 0.18
    out_w = 0.43
    out_gap = 0.04
    out_x0 = (1 - (2 * out_w + out_gap)) / 2

    # left: regret bounds (theory)
    box(ax, out_x0, out_y, out_w, out_h, C_THEORY,
        text="", textcolor="white", radius=0.012, alpha=0.95)
    ax.text(out_x0 + out_w / 2, out_y + out_h - 0.022,
            "Regret (theory)", ha="center", va="center",
            fontsize=4.5, fontweight="bold", color="white")
    ax.text(out_x0 + out_w / 2, out_y + out_h - 0.06,
            "Stationary:", ha="center", va="center", fontsize=3.5, color="white")
    ax.text(out_x0 + out_w / 2, out_y + out_h - 0.09,
            r"$O(\sqrt{T \log T})$", ha="center", va="center",
            fontsize=5.5, fontweight="bold", color="white")
    ax.text(out_x0 + out_w / 2, out_y + out_h - 0.125,
            "Non-stationary:", ha="center", va="center", fontsize=3.5, color="white")
    ax.text(out_x0 + out_w / 2, out_y + out_h - 0.16,
            r"$\Omega(\sqrt{KT})$", ha="center", va="center",
            fontsize=5.5, fontweight="bold", color="white")

    # right: empirical outcomes
    box(ax, out_x0 + out_w + out_gap, out_y, out_w, out_h, C_RESULT,
        text="", textcolor="white", radius=0.012, alpha=0.95)
    ax.text(out_x0 + out_w + out_gap + out_w / 2, out_y + out_h - 0.022,
            "Empirical (8 seeds)", ha="center", va="center",
            fontsize=4, fontweight="bold", color="white")
    ax.text(out_x0 + out_w + out_gap + out_w / 2, out_y + out_h - 0.06,
            "8-UAV:", ha="center", va="center", fontsize=3.5, color="white")
    ax.text(out_x0 + out_w + out_gap + out_w / 2, out_y + out_h - 0.095,
            r"$\uparrow$ +16.8%  (p = 0.018)",
            ha="center", va="center", fontsize=4.5, fontweight="bold", color="white")
    ax.text(out_x0 + out_w + out_gap + out_w / 2, out_y + out_h - 0.135,
            "Simpler DMO:", ha="center", va="center", fontsize=3.5, color="white")
    ax.text(out_x0 + out_w + out_gap + out_w / 2, out_y + out_h - 0.165,
            r"$\downarrow$  no benefit",
            ha="center", va="center", fontsize=4.5, fontweight="bold", color="white")

    # ===== Take-home strip (bottom) =====
    ax.text(0.5, 0.12,
            "Aggressive LLM > pure DE  >  Conservative LLM",
            ha="center", va="center", fontsize=4.2, fontweight="bold", color=C_TEXT)
    ax.text(0.5, 0.085,
            "LLM calls: 5--15% of generations",
            ha="center", va="center", fontsize=3.8, color="#555")
    ax.text(0.5, 0.05,
            "Qwen-2.5-7B  /  Qwen-3.5-9B  /  OmniCoder-9B",
            ha="center", va="center", fontsize=3.3, color="#777")

    out_path = FIG_DIR / "graphical_abstract.png"
    fig.savefig(out_path, dpi=600, facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"graphical abstract written to: {out_path}")
    print(f"  size on disk: {out_path.stat().st_size / 1024:.1f} KB")
    print(f"  print size:   5 x 5 cm @ 600 dpi = 1181 x 1181 px")


if __name__ == "__main__":
    main()
