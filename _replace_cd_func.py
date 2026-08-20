# -*- coding: utf-8 -*-
"""
Replace the plot_cd_diagram function body with a cleaner layout:
- Data-tight xlim (no wasted white margins)
- No bottom-axis tick numbers (avoid duplicate '1 2 3 4' labels)
- CD bar moved BELOW the axis
- Clique bars moved ABOVE the axis (just below the lowest label)
"""
PATH = r"D:\新论文\实验\experiments\stats_ablation_crossllm.py"

with open(PATH, "r", encoding="utf-8") as f:
    src = f.read()

old_func = '''def plot_cd_diagram(sorted_keys, ranks, cd, k, N, title, out_png, out_pdf,
                    color_map, label_map):
    """Draw a Nemenyi CD diagram with clique bars."""
    mpl.rcParams.update({
        'font.family': 'DejaVu Serif',
        'font.size': 10,
        'savefig.dpi': 300,
    })
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.set_xlim(0.2, k + 0.8)
    ax.set_ylim(-0.95, 2.05)
    ax.set_xticks(range(1, k + 1))
    ax.set_yticks([])

    # Bottom axis
    for x in range(1, k + 1):
        ax.plot([x, x], [0.0, 0.08], color='black', lw=0.8, zorder=2)
        ax.text(x, -0.12, str(x), ha='center', va='top', fontsize=9)

    # CD bar
    cd_y = 1.85
    ax.plot([1, cd + 1], [cd_y, cd_y], color='black', lw=1.3)
    ax.plot([1, 1], [cd_y - 0.06, cd_y + 0.06], color='black', lw=1.3)
    ax.plot([cd + 1, cd + 1], [cd_y - 0.06, cd_y + 0.06], color='black', lw=1.3)
    ax.text(1 + cd / 2, cd_y + 0.10, f'CD = {cd:.2f}', ha='center', va='bottom',
            fontsize=9.5)

    # Markers + labels: use 6 vertical levels with sufficient gap to avoid
    # overlap for both 3-LLM (close ranks) and 4-version (split ranks) cases.
    label_y = {}
    overlap_threshold = 0.7
    sorted_pairs = sorted(enumerate(sorted_keys), key=lambda p: ranks[p[0]])
    y_levels = [0.55, 0.90, 1.25, 1.60]
    for idx, key in sorted_pairs:
        r = ranks[idx]
        placed = False
        for y_off in y_levels:
            collide = False
            for prev_key, (px, py) in label_y.items():
                if abs(r - px) < overlap_threshold and abs(y_off - py) < 0.20:
                    collide = True
                    break
            if not collide:
                label_y[key] = (r, y_off)
                placed = True
                break
        if not placed:
            label_y[key] = (r, y_levels[0])

    for key, rank in zip(sorted_keys, ranks):
        _, y_off = label_y[key]
        ax.plot(rank, 0.20, 'o', ms=12, color=color_map[key],
                mec='black', mew=0.8, zorder=3)
        ax.plot([rank, rank], [0.20, y_off - 0.05], color='gray', lw=0.6, zorder=2)
        # Use vertical alignment top and offset y to compensate for label height
        ax.text(rank, y_off, label_map[key], ha='center', va='bottom',
                fontsize=9.0, fontweight='bold')

    # Cliques
    cliques = []
    cur = [sorted_keys[0]]
    for kk in sorted_keys[1:]:
        if abs(ranks[sorted_keys.index(kk)] - ranks[sorted_keys.index(cur[0])]) <= cd:
            cur.append(kk)
        else:
            cliques.append(cur)
            cur = [kk]
    cliques.append(cur)
    clique_y = -0.55
    for clique in cliques:
        if len(clique) > 1:
            x_min = min(ranks[sorted_keys.index(c)] for c in clique) - 0.05
            x_max = max(ranks[sorted_keys.index(c)] for c in clique) + 0.05
            ax.plot([x_min, x_max], [clique_y, clique_y], color='#aa3322', lw=2.5, zorder=3)
            ax.plot([x_min, x_min], [clique_y - 0.04, clique_y + 0.04], color='#aa3322', lw=2.5)
            ax.plot([x_max, x_max], [clique_y - 0.04, clique_y + 0.04], color='#aa3322', lw=2.5)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.set_xlabel('Average Friedman rank (lower is better)', fontsize=10)
    fig.suptitle(title, fontsize=10.5, y=1.05)
    fig.tight_layout()
    fig.savefig(out_png, bbox_inches='tight')
    fig.savefig(out_pdf, bbox_inches='tight')
    plt.close(fig)'''

new_func = '''def plot_cd_diagram(sorted_keys, ranks, cd, k, N, title, out_png, out_pdf,
                    color_map, label_map):
    """Draw a Nemenyi CD diagram with clique bars.

    Layout (T66 redesign):
      - Data-tight xlim so clustered ranks don't sit in a 50% white margin
      - NO bottom-axis tick numbers (avoid duplicate "1 2 3 4" labels)
      - CD reference bar placed BELOW the axis
      - Clique bars placed ABOVE the axis, just below the labels
      - Wider x-overlap threshold so clustered ranks (e.g. 2.143 & 2.214)
        are forced to different y-levels
    """
    mpl.rcParams.update({
        'font.family': 'DejaVu Serif',
        'font.size': 10,
        'savefig.dpi': 300,
    })
    fig, ax = plt.subplots(figsize=(7.0, 3.4))

    # Data-tight xlim: avoid large white margins when ranks are clustered
    rmin = min(ranks)
    rmax = max(ranks)
    pad = 0.55
    x_lo = max(0.5, rmin - pad)
    x_hi = rmax + pad
    ax.set_xlim(x_lo, x_hi)
    ax.set_ylim(-1.15, 1.85)
    ax.set_yticks([])

    # Bottom axis: single horizontal line (no per-tick numbers)
    ax.plot([x_lo, x_hi], [0.0, 0.0], color='black', lw=0.8, zorder=2)
    for x in range(max(1, int(x_lo)), int(x_hi) + 1):
        ax.plot([x, x], [0.0, 0.07], color='black', lw=0.8, zorder=2)

    # CD reference bar BELOW the axis, anchored at rank coordinates
    cd_y = -0.60
    cd_x_lo = rmin + 0.10
    cd_x_hi = cd_x_lo + cd
    ax.plot([cd_x_lo, cd_x_hi], [cd_y, cd_y], color='black', lw=1.5, zorder=3)
    ax.plot([cd_x_lo, cd_x_lo], [cd_y - 0.05, cd_y + 0.05], color='black', lw=1.5, zorder=3)
    ax.plot([cd_x_hi, cd_x_hi], [cd_y - 0.05, cd_y + 0.05], color='black', lw=1.5, zorder=3)
    ax.text((cd_x_lo + cd_x_hi) / 2, cd_y + 0.10, f'CD = {cd:.2f}',
            ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Markers + labels: greedy vertical placement with 4 y-levels
    label_y = {}
    x_overlap_thr = 0.35
    y_overlap_thr = 0.18
    sorted_pairs = sorted(enumerate(sorted_keys), key=lambda p: ranks[p[0]])
    y_levels = [0.55, 0.95, 1.35, 1.75]
    for idx, key in sorted_pairs:
        r = ranks[idx]
        placed = False
        for y_off in y_levels:
            collide = False
            for prev_key, (px, py) in label_y.items():
                if abs(r - px) < x_overlap_thr and abs(y_off - py) < y_overlap_thr:
                    collide = True
                    break
            if not collide:
                label_y[key] = (r, y_off)
                placed = True
                break
        if not placed:
            label_y[key] = (r, y_levels[0])

    for key, rank in zip(sorted_keys, ranks):
        _, y_off = label_y[key]
        # Marker
        ax.plot(rank, 0.20, 'o', ms=13, color=color_map[key],
                mec='black', mew=0.9, zorder=4)
        # Connector line
        ax.plot([rank, rank], [0.20, y_off - 0.04], color='gray', lw=0.6, zorder=2)
        # Label
        ax.text(rank, y_off, label_map[key], ha='center', va='bottom',
                fontsize=9.5, fontweight='bold')

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
    # Clique bars ABOVE the axis, just below the lowest label
    clique_y = 0.40
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
    ax.set_xlabel('Average Friedman rank (lower is better)', fontsize=10)
    fig.suptitle(title, fontsize=10.5, y=1.02)
    fig.tight_layout()
    fig.savefig(out_png, bbox_inches='tight')
    fig.savefig(out_pdf, bbox_inches='tight')
    plt.close(fig)'''

if old_func in src:
    new_src = src.replace(old_func, new_func)
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(new_src)
    print(f"[cd-fix] replaced plot_cd_diagram ({len(new_func) - len(old_func):+d} chars)")
else:
    print("[cd-fix] old function not found verbatim; aborting")
