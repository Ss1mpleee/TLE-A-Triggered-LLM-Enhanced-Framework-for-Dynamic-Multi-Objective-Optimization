#!/usr/bin/env python
"""Add annotations to fig_ablation_lite.png for the 'blank' panels:
- DF9, DF14: all 30 seeds = IGD 0.0 (3-obj success, LLM unnecessary)
- DF10: boxes are at IGD 40-60, completely off the y=2.0 clip
- DF11: V0 (T0) is degenerate at IGD=1.0 (3-obj failure floor), boxes
  for T1/T2/T3 are tight at 1.0-1.4 (small but visible)

Approach: read the existing script, patch the panel-A annotation block
to add a small 'off-chart' / 'all-zero' callout below the x-axis for
DF9/DF10/DF11/DF14, then re-run the figure generation.
"""
from pathlib import Path
import re
import subprocess

# Run the existing plot script first to regenerate the figure with
# the new annotations in place.  We'll do the annotation insertion
# via a wrapper that imports + monkey-patches.

PLOT_SCRIPT = Path(r'D:\新论文\实验\experiments\plot_ablation_lite.py')

# Read current script
code = PLOT_SCRIPT.read_text(encoding='utf-8')

# Locate the catastrophic-annotation block (after T0 lock annotation)
# and insert off-chart / all-zero annotations just before plt.tight_layout()
old_block = '''# Catastrophic annotation (top-right)
if catastrophic:
    cat_lines = []
    for (ver, prob), (cnt, vals) in sorted(catastrophic.items()):
        max_v = max(vals)
        if max_v > 5:
            cat_lines.append(f"{ver.replace('_', ' ')}/{prob}: "
                             f"{cnt}/30 catastrophic, max IGD={max_v:.0f}")
    if cat_lines:
        cat_text = "Catastrophic (clipped at 2.0):\\n" + "\\n".join(cat_lines[:4])
        ax.text(0.99, 0.97, cat_text, transform=ax.transAxes,
                ha='right', va='top', fontsize=7.5,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffe0e0',
                          edgecolor='#aa3322', alpha=0.85))'''

new_block = '''# Catastrophic annotation (top-right)
if catastrophic:
    cat_lines = []
    for (ver, prob), (cnt, vals) in sorted(catastrophic.items()):
        max_v = max(vals)
        if max_v > 5:
            cat_lines.append(f"{ver.replace('_', ' ')}/{prob}: "
                             f"{cnt}/30 catastrophic, max IGD={max_v:.0f}")
    if cat_lines:
        cat_text = "Catastrophic (clipped at 2.0):\\n" + "\\n".join(cat_lines[:4])
        ax.text(0.99, 0.97, cat_text, transform=ax.transAxes,
                ha='right', va='top', fontsize=7.5,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffe0e0',
                          edgecolor='#aa3322', alpha=0.85))

# Per-problem annotations for the 3-obj cases that look 'blank' due to
# clip or degenerate IGD distribution.  These explain why the visible
# box is flat or absent, so the reader does not interpret them as
# missing data.
off_chart_msgs = []
for prob in probs:
    if prob not in ('DF9', 'DF10', 'DF11', 'DF14'):
        continue
    # Compute the data range for this problem across all 4 versions
    all_max = 0.0
    all_min = float('inf')
    for ver in VERSIONS:
        rs = by_vp.get((ver, prob), [])
        if rs:
            igds = [r['igd'] for r in rs if r.get('igd') is not None]
            if igds:
                all_max = max(all_max, max(igds))
                all_min = min(all_min, min(igds))
    pi = probs.index(prob)
    gc = group_centers[pi]
    if all_max < 0.01:
        # All-zero case (DF9, DF14)
        ax.text(gc, 0.05,
                'all 30 seeds\\n= 0.0\\n(3-obj solved)',
                ha='center', va='bottom', fontsize=6.5,
                color='#226622', style='italic',
                bbox=dict(boxstyle='round,pad=0.2',
                          facecolor='#eeffee', edgecolor='#88aa88',
                          alpha=0.85))
    elif all_min >= 1.0 and all_max < 2.0:
        # DF11: 3-obj failure floor, all locked at 1.0
        ax.text(gc, 0.55,
                'all 30 seeds\\n$\\\\geq$ 1.0\\n(3-obj failure floor)',
                ha='center', va='top', fontsize=6.5,
                color='#444444', style='italic',
                bbox=dict(boxstyle='round,pad=0.2',
                          facecolor='#eeeeee', edgecolor='#888888',
                          alpha=0.85))
    elif all_max > CLIP_Y:
        # DF10: off-chart catastrophic
        ax.text(gc, 1.85,
                f'ALL OFF-CHART\\n4 versions × 30 seeds\\nIGD = {all_min:.0f}–{all_max:.0f}\\n(3-obj catastrophic)',
                ha='center', va='top', fontsize=7, color='#aa2222',
                fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.25',
                          facecolor='#ffeeee', edgecolor='#cc3333',
                          alpha=0.92))'''

if old_block in code:
    code = code.replace(old_block, new_block)
    PLOT_SCRIPT.write_text(code, encoding='utf-8')
    print("Patched plot_ablation_lite.py with new annotations")
else:
    print("ERROR: old block not found in plot script")
    raise SystemExit(1)
