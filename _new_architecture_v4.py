#!/usr/bin/env python
"""
T68 v4 (rev2): TLE Framework figure - clean, journal-quality redesign.

Layout: 18x9 inches, three-column architecture with annotated process flow.
"""
from __future__ import annotations
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch, Circle
import matplotlib as mpl
from pathlib import Path
import shutil

mpl.rcParams['font.family'] = 'DejaVu Serif'
mpl.rcParams['font.size'] = 10
mpl.rcParams['savefig.dpi'] = 300

# ---- Style constants ------------------------------------------------------
C_DMO_FILL, C_DMO_EDGE = '#e2e8f0', '#475569'
C_L1_FILL, C_L1_EDGE   = '#dbeafe', '#1d4ed8'
C_L2_FILL, C_L2_EDGE   = '#d1fae5', '#047857'
C_L3_FILL, C_L3_EDGE   = '#ffedd5', '#c2410c'
C_TRIG_FILL, C_TRIG_EDGE = '#fef3c7', '#a16207'
C_CODE_BG = '#0f172a'
C_CODE_TXT = '#e2e8f0'
C_CODE_KEY = '#93c5fd'
C_CODE_STR = '#86efac'
C_CODE_NUM = '#fbbf24'

# ---- Figure setup ---------------------------------------------------------
fig = plt.figure(figsize=(18, 9.5))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 18)
ax.set_ylim(0, 10)
ax.set_aspect('equal')
ax.axis('off')

# ---- Helpers --------------------------------------------------------------
def shadow_box(x, y, w, h, fc, ec, lw=1.6, r=0.10, sh_off=0.04, sh_alpha=0.18):
    s = FancyBboxPatch((x + sh_off, y - sh_off), w, h,
                       boxstyle=f'round,pad=0.02,rounding_size={r}',
                       linewidth=0, facecolor='black', alpha=sh_alpha, zorder=1)
    ax.add_patch(s)
    b = FancyBboxPatch((x, y), w, h,
                       boxstyle=f'round,pad=0.02,rounding_size={r}',
                       linewidth=lw, facecolor=fc, edgecolor=ec, zorder=2)
    ax.add_patch(b)
    return b

def header_bar(x, y, w, h, fc, title_left, title_right, title_l_color='white', title_r_color='white'):
    bar = FancyBboxPatch((x, y), w, h,
                         boxstyle='round,pad=0.02,rounding_size=0.08',
                         facecolor=fc, edgecolor='none', zorder=3)
    ax.add_patch(bar)
    # bottom rectangle to make the bar only have rounded TOP corners is complex;
    # just use rectangle
    return bar

def arrow(x1, y1, x2, y2, color='#1f2937', lw=1.8, style='-', mutation=18):
    a = FancyArrowPatch((x1, y1), (x2, y2),
                        arrowstyle='-|>', mutation_scale=mutation,
                        linewidth=lw, color=color, linestyle=style,
                        connectionstyle='arc3', zorder=3)
    ax.add_patch(a)

# ============================================================================
# TITLE BAR
# ============================================================================
ax.text(9.0, 9.55, 'TLE: Triggered LLM-Enhanced Evolutionary Framework',
        ha='center', va='center', fontsize=22, fontweight='bold', color='#0f172a')
ax.text(9.0, 9.10, 'Event-Driven LLM-EC for Dynamic Multi-Objective Optimization',
        ha='center', va='center', fontsize=12.5, style='italic', color='#475569')
ax.plot([4.5, 13.5], [8.78, 8.78], color='#94a3b8', linewidth=0.8, zorder=2)

# ============================================================================
# LEFT COLUMN — DMO Problem (input)
# ============================================================================
LX, LY, LW, LH = 0.5, 0.85, 3.4, 7.20
shadow_box(LX, LY, LW, LH, C_DMO_FILL, C_DMO_EDGE, lw=2.0, r=0.15)
# Header bar
hb = Rectangle((LX, LY + LH - 0.80), LW, 0.80, facecolor=C_DMO_EDGE, edgecolor='none', zorder=3)
ax.add_patch(hb)
ax.text(LX + LW/2, LY + LH - 0.42, 'DMO Problem',
        ha='center', va='center', fontsize=14, fontweight='bold', color='white')
ax.text(LX + LW/2, LY + LH - 0.70, 'INPUT SPECIFICATION',
        ha='center', va='center', fontsize=8.5, color='#cbd5e1', family='monospace')

# spec rows
spec_lines = [
    ('Benchmark',       'CEC 2018 DMO'),
    ('Problems',        'DF1 — DF14'),
    ('Env. change',     'τ = 10 gens'),
    ('Obj. dimension',  'n_env = 3'),
    ('Population',      'NP = 50'),
    ('Generations',     'T = 200'),
    ('Fleet scale',     '4 / 8 / 16 / 32'),
    ('Repetitions',     'n = 30 / prob.'),
    ('Pareto metric',   'IGD'),
]
y0 = LY + LH - 1.30
for label, val in spec_lines:
    ax.text(LX + 0.22, y0, label, ha='left', va='center',
            fontsize=9.5, color='#334155', fontweight='bold')
    ax.text(LX + LW - 0.22, y0, val, ha='right', va='center',
            fontsize=9.5, color='#0f172a', family='monospace')
    y0 -= 0.50

# divider
ax.plot([LX + 0.22, LX + LW - 0.22], [y0 + 0.18, y0 + 0.18],
        color='#cbd5e1', linewidth=0.7, zorder=3)
# input tag
tag = FancyBboxPatch((LX + 0.70, LY + 0.32), LW - 1.4, 0.50,
                     boxstyle='round,pad=0.02,rounding_size=0.10',
                     facecolor=C_DMO_EDGE, edgecolor='none', zorder=3)
ax.add_patch(tag)
ax.text(LX + LW/2, LY + 0.57, '[ INPUT ]', ha='center', va='center',
        fontsize=11, fontweight='bold', color='white', family='monospace')

# ============================================================================
# CENTER COLUMN — 3 layers
# ============================================================================
CX, CW = 4.3, 8.4
# Layer 3 (top): Budget Scheduler
L3X, L3Y, L3W, L3H = CX, 6.20, CW, 1.65
shadow_box(L3X, L3Y, L3W, L3H, C_L3_FILL, C_L3_EDGE, lw=2.0, r=0.12)
hd = Rectangle((L3X, L3Y + L3H - 0.45), L3W, 0.45, facecolor=C_L3_EDGE, edgecolor='none', zorder=3)
ax.add_patch(hd)
ax.text(L3X + 0.30, L3Y + L3H - 0.22, 'Layer 3',
        ha='left', va='center', fontsize=11, fontweight='bold', color='white', family='monospace')
ax.text(L3X + L3W - 0.30, L3Y + L3H - 0.22, 'Budget Scheduler',
        ha='right', va='center', fontsize=13, fontweight='bold', color='white')
ax.text(L3X + L3W/2, L3Y + L3H - 0.78,
        'UCB1 multi-armed bandit  ·  per-signal, per-generation',
        ha='center', va='center', fontsize=10.5, color='#0f172a')
ax.text(L3X + L3W/2, L3Y + L3H - 1.08,
        'B = T / τ    ·    cap = 50 calls / run',
        ha='center', va='center', fontsize=10.5, family='monospace', color='#0f172a')
ax.text(L3X + L3W/2, L3Y + L3H - 1.38,
        'Adaptive decision:  invoke LLM ?     (yes / no)',
        ha='center', va='center', fontsize=10, style='italic', color=C_L3_EDGE, fontweight='bold')

# Arrow L3 → L2
arrow(L3X + L3W/2, L3Y, L3X + L3W/2, L3Y - 0.30, color=C_L3_EDGE, lw=2.2)
ax.text(L3X + L3W/2 + 0.25, L3Y - 0.15, 'allow?', ha='left', va='center',
        fontsize=9.5, color=C_L3_EDGE, style='italic', fontweight='bold')

# Layer 2 — LLM Strategic Advisor
L2X, L2Y, L2W, L2H = CX, 2.80, CW, 3.05
shadow_box(L2X, L2Y, L2W, L2H, C_L2_FILL, C_L2_EDGE, lw=2.0, r=0.12)
hd = Rectangle((L2X, L2Y + L2H - 0.45), L2W, 0.45, facecolor=C_L2_EDGE, edgecolor='none', zorder=3)
ax.add_patch(hd)
ax.text(L2X + 0.30, L2Y + L2H - 0.22, 'Layer 2',
        ha='left', va='center', fontsize=11, fontweight='bold', color='white', family='monospace')
ax.text(L2X + L2W - 0.30, L2Y + L2H - 0.22, 'LLM Strategic Advisor',
        ha='right', va='center', fontsize=13, fontweight='bold', color='white')
ax.text(L2X + L2W/2, L2Y + L2H - 0.78,
        'Local LLM via Ollama   ·   Qwen-2.5-7B-Instruct (chat-tuned)',
        ha='center', va='center', fontsize=10, color='#0f172a')

# JSON code block
JSON_X, JSON_Y, JSON_W, JSON_H = L2X + 0.40, L2Y + 0.78, L2W - 0.80, 1.55
sj = FancyBboxPatch((JSON_X + 0.04, JSON_Y - 0.04), JSON_W, JSON_H,
                    boxstyle='round,pad=0.02,rounding_size=0.06',
                    facecolor='black', alpha=0.22, zorder=3)
ax.add_patch(sj)
jc = FancyBboxPatch((JSON_X, JSON_Y), JSON_W, JSON_H,
                    boxstyle='round,pad=0.02,rounding_size=0.06',
                    facecolor=C_CODE_BG, edgecolor='#334155', linewidth=1.0, zorder=4)
ax.add_patch(jc)

# JSON content as one string with colored spans using a custom approach
# Use multiple text() calls per line for coloring
json_lines = [
    ('> JSON dual-channel output:',         'header'),
    ('{',                                   'punct'),
    ('  "strategy":',                       'key'),
    ('  "explore",',                        'str'),
    ('  "F":',                              'key'),
    ('  0.65,',                             'num'),
    ('  "CR":',                             'key'),
    ('  0.85,',                             'num'),
    ('  "rationale":',                      'key'),
    ('  "..."',                             'str'),
    ('}',                                   'punct'),
]
y = JSON_Y + JSON_H - 0.18
x = JSON_X + 0.18
line_h = 0.12
for txt, kind in json_lines:
    if kind == 'header':
        ax.text(x, y, txt, ha='left', va='center',
                fontsize=9.5, color='#fbbf24', family='monospace',
                fontweight='bold', zorder=5)
    elif kind == 'key':
        ax.text(x, y, txt, ha='left', va='center',
                fontsize=9.5, color=C_CODE_KEY, family='monospace', zorder=5)
    elif kind == 'str':
        ax.text(x, y, txt, ha='left', va='center',
                fontsize=9.5, color=C_CODE_STR, family='monospace', zorder=5)
    elif kind == 'num':
        ax.text(x, y, txt, ha='left', va='center',
                fontsize=9.5, color=C_CODE_NUM, family='monospace', zorder=5)
    else:
        ax.text(x, y, txt, ha='left', va='center',
                fontsize=9.5, color=C_CODE_TXT, family='monospace', zorder=5)
    y -= line_h

# Layer 2 footer — dual-channel labels
ax.text(L2X + L2W/2, L2Y + 0.50,
        'Channel 1 (strategic)  :  operator mode  ·  search focus',
        ha='center', va='center', fontsize=9, color='#0f172a', family='monospace')
ax.text(L2X + L2W/2, L2Y + 0.25,
        'Channel 2 (parametric) :  F ∈ [0.3, 0.9]   CR ∈ [0.5, 1.0]',
        ha='center', va='center', fontsize=9, color='#0f172a', family='monospace')

# Arrow L2 → L1
arrow(L2X + L2W/2, L2Y, L2X + L2W/2, L2Y - 0.30, color=C_L2_EDGE, lw=2.2)
ax.text(L2X + L3W/2 + 0.25, L2Y - 0.15, 'F, CR, mode', ha='left', va='center',
        fontsize=9.5, color=C_L2_EDGE, style='italic', fontweight='bold')

# Layer 1 — DE/NSGA-II Search Engine
L1X, L1Y, L1W, L1H = CX, 0.85, CW, 1.65
shadow_box(L1X, L1Y, L1W, L1H, C_L1_FILL, C_L1_EDGE, lw=2.0, r=0.12)
hd = Rectangle((L1X, L1Y + L1H - 0.45), L1W, 0.45, facecolor=C_L1_EDGE, edgecolor='none', zorder=3)
ax.add_patch(hd)
ax.text(L1X + 0.30, L1Y + L1H - 0.22, 'Layer 1',
        ha='left', va='center', fontsize=11, fontweight='bold', color='white', family='monospace')
ax.text(L1X + L1W - 0.30, L1Y + L1H - 0.22, 'DE / NSGA-II Search Engine',
        ha='right', va='center', fontsize=13, fontweight='bold', color='white')

# 4 sub-pipeline boxes (bigger, more breathing room)
SUB_Y, SUB_H = L1Y + 0.20, 0.85
sub_w = (L1W - 0.90 - 3 * 0.15) / 4
sub_x = L1X + 0.45
sub_specs = [
    ('Population',  'NP = 50'),
    ('DE / rand/1/bin', 'F, CR ← LLM'),
    ('Evaluate',  'f_1, f_2'),
    ('NSGA-II',  'non-dom. sort'),
]
for i, (label, sub) in enumerate(sub_specs):
    bx = sub_x + i * (sub_w + 0.15)
    sb = FancyBboxPatch((bx + 0.03, SUB_Y - 0.03), sub_w, SUB_H,
                        boxstyle='round,pad=0.02,rounding_size=0.06',
                        facecolor='black', alpha=0.18, zorder=3)
    ax.add_patch(sb)
    pb = FancyBboxPatch((bx, SUB_Y), sub_w, SUB_H,
                        boxstyle='round,pad=0.02,rounding_size=0.06',
                        facecolor='white', edgecolor=C_L1_EDGE, linewidth=1.4, zorder=4)
    ax.add_patch(pb)
    # Label
    ax.text(bx + sub_w/2, SUB_Y + SUB_H - 0.30, label,
            ha='center', va='center', fontsize=10, fontweight='bold', color=C_L1_EDGE, zorder=6)
    # Sub
    ax.text(bx + sub_w/2, SUB_Y + 0.25, sub,
            ha='center', va='center', fontsize=8.5, color='#475569', family='monospace', style='italic', zorder=6)
    # Arrow to next
    if i < 3:
        arrow(bx + sub_w + 0.01, SUB_Y + SUB_H/2, bx + sub_w + 0.14, SUB_Y + SUB_H/2,
              color=C_L1_EDGE, lw=1.5, mutation=12)

# ============================================================================
# RIGHT COLUMN — Triple-Signal Trigger
# ============================================================================
RX, RY, RW, RH = 13.1, 1.55, 4.5, 6.50
shadow_box(RX, RY, RW, RH, C_TRIG_FILL, C_TRIG_EDGE, lw=2.5, r=0.15)
# Header bar
hb = FancyBboxPatch((RX, RY + RH - 0.75), RW, 0.75,
                    boxstyle='round,pad=0.02,rounding_size=0.15',
                    facecolor=C_TRIG_EDGE, edgecolor='none', zorder=3)
ax.add_patch(hb)
ax.text(RX + RW/2, RY + RH - 0.32, 'Triple-Signal Trigger',
        ha='center', va='center', fontsize=14, fontweight='bold', color='white')
ax.text(RX + RW/2, RY + RH - 0.60, '( core contribution )',
        ha='center', va='center', fontsize=10, style='italic', color='#fef3c7')

# 3 signal cards
SIG_H = 1.20
GAP = 0.25
sig_y = RY + RH - 0.90 - SIG_H
sigs = [
    ('S1', 'Entropy Descent',     'H(P_t) < 0.95 · H(P_t-1)',          '▼', '#dc2626'),
    ('S2', 'Fitness Stagnation',  'Δf < 1e-3  for  w = 8  gens',       '—', '#0891b2'),
    ('S3', 'Environmental Change','|f_t - f_{t-1}| / |f_{t-1}| > 0.05', '*', '#7c3aed'),
]
for i, (tag, name, formula, icon, icon_color) in enumerate(sigs):
    cy = sig_y - i * (SIG_H + GAP)
    sb = FancyBboxPatch((RX + 0.20 + 0.04, cy - 0.04), RW - 0.40, SIG_H,
                        boxstyle='round,pad=0.02,rounding_size=0.08',
                        facecolor='black', alpha=0.18, zorder=3)
    ax.add_patch(sb)
    cb = FancyBboxPatch((RX + 0.20, cy), RW - 0.40, SIG_H,
                        boxstyle='round,pad=0.02,rounding_size=0.08',
                        facecolor='white', edgecolor=C_TRIG_EDGE, linewidth=1.2, zorder=4)
    ax.add_patch(cb)
    # Icon circle (left)
    icon_circ = Circle((RX + 0.60, cy + SIG_H * 0.62), 0.30,
                       facecolor=icon_color, edgecolor='white', linewidth=1.5, zorder=5)
    ax.add_patch(icon_circ)
    ax.text(RX + 0.60, cy + SIG_H * 0.62, icon,
            ha='center', va='center', fontsize=16, fontweight='bold', color='white', zorder=6)
    # Tag
    ax.text(RX + 1.05, cy + SIG_H * 0.78, tag,
            ha='left', va='center', fontsize=11, fontweight='bold',
            color=icon_color, family='monospace', zorder=6)
    # Name
    ax.text(RX + 1.55, cy + SIG_H * 0.78, name,
            ha='left', va='center', fontsize=10.5, fontweight='bold', color='#0f172a', zorder=6)
    # Formula (centered, full width)
    ax.text(RX + (RW - 0.40) / 2 + 0.20, cy + SIG_H * 0.32, formula,
            ha='center', va='center', fontsize=10, color='#0f172a', family='monospace', zorder=6)

# OR gate (below S3, above button)
or_y = RY + 0.65
or_box = FancyBboxPatch((RX + RW/2 - 0.40, or_y), 0.80, 0.42,
                        boxstyle='round,pad=0.02,rounding_size=0.10',
                        facecolor='#fde68a', edgecolor=C_TRIG_EDGE, linewidth=1.5, zorder=4)
ax.add_patch(or_box)
ax.text(RX + RW/2, or_y + 0.21, 'OR', ha='center', va='center',
        fontsize=15, fontweight='bold', color='#7c2d12', zorder=6)

# trigger fires button
btn = FancyBboxPatch((RX + 0.30, RY + 0.10), RW - 0.60, 0.45,
                     boxstyle='round,pad=0.02,rounding_size=0.10',
                     facecolor='#dc2626', edgecolor='#7f1d1d', linewidth=1.2, zorder=4)
ax.add_patch(btn)
ax.text(RX + RW/2, RY + 0.32, '→  trigger fires',
        ha='center', va='center', fontsize=12, fontweight='bold', color='white', zorder=6)

# Empirical cost line (below trigger box)
ax.text(RX + RW/2, RY - 0.10,
        'fires on  9.7 – 38.9 %  of generations',
        ha='center', va='center', fontsize=9.5, color='#7c2d12',
        style='italic', fontweight='bold')
ax.text(RX + RW/2, RY - 0.32,
        '(IQR 15.4 – 23.5 %,  mean 19.3 %  on 14 CEC 2018 problems)',
        ha='center', va='center', fontsize=8.5, color='#7c2d12', style='italic')

# ============================================================================
# CROSS-COLUMN ARROWS
# ============================================================================
# Trigger → Layer 3 (allow?)
arrow(RX, RY + 0.45, L3X + L3W + 0.04, L3Y + L3H * 0.50,
      color='#dc2626', lw=2.4, mutation=22)
# "fires" label
ax.text(RX - 0.10, RY + 0.55, 'fires',
        ha='right', va='center', fontsize=11, fontweight='bold',
        color='#dc2626', style='italic',
        bbox=dict(boxstyle='round,pad=0.20', facecolor='white',
                  edgecolor='#dc2626', linewidth=0.8, alpha=0.95), zorder=6)

# Layer 1 → Trigger (stats / Δf, feedback)
arrow(L1X + L1W + 0.04, L1Y + L1H * 0.55, RX, L1Y + L1H * 0.55 + 0.30,
      color='#7c3aed', lw=1.6, style='--', mutation=16)
ax.text((L1X + L1W + RX)/2 - 0.20, L1Y + L1H * 0.55 - 0.10, 'stats / Δf',
        ha='center', va='center', fontsize=9, color='#7c3aed', style='italic',
        bbox=dict(boxstyle='round,pad=0.18', facecolor='white',
                  edgecolor='none', alpha=0.85), zorder=5)

# ============================================================================
# BOTTOM STRIP — Empirical cost summary
# ============================================================================
BSX, BSY, BSW, BSH = 0.5, 0.10, 12.2, 0.65
sb = FancyBboxPatch((BSX, BSY), BSW, BSH,
                    boxstyle='round,pad=0.02,rounding_size=0.06',
                    facecolor='#ecfdf5', edgecolor='#059669', linewidth=1.3, zorder=2)
ax.add_patch(sb)
metrics = [
    ('TLE ≈ 38.6 calls / run',      '(19.3 % of 200 gens, IQR 15.4 – 23.5 %)',     C_L3_EDGE),
    ('Cost-norm. IGD:  2.37 ×',     'better than DE-LM-static  (18.9 vs 44.9 / 1000 calls)', '#0e7490'),
    ('Multi-UAV:  19.0 – 21.2 %',   'task-cost reduction vs DNSGA-II-A   (p ≤ 0.0312)',     '#7c3aed'),
]
seg_w = BSW / 3
for i, (m, sub, c) in enumerate(metrics):
    sx = BSX + i * seg_w
    ax.text(sx + seg_w/2, BSY + 0.42, m,
            ha='center', va='center', fontsize=10, fontweight='bold', color=c)
    ax.text(sx + seg_w/2, BSY + 0.16, sub,
            ha='center', va='center', fontsize=8.2, color='#0f172a', style='italic')
    if i < 2:
        ax.plot([sx + seg_w, sx + seg_w], [BSY + 0.10, BSY + BSH - 0.10],
                color='#94a3b8', linewidth=0.6, zorder=3)

# Legend
ax.text(13.1, BSY + 0.42, 'Legend:', ha='left', va='center',
        fontsize=9.5, fontweight='bold', color='#0f172a')
# arrow symbols with labels
ax.add_patch(FancyArrowPatch((14.0, BSY + 0.40), (14.4, BSY + 0.40),
                              arrowstyle='-|>', mutation_scale=10,
                              color='#1f2937', linewidth=1.4))
ax.text(14.5, BSY + 0.40, 'data flow', ha='left', va='center', fontsize=8.5, color='#0f172a')
ax.add_patch(FancyArrowPatch((14.0, BSY + 0.18), (14.4, BSY + 0.18),
                              arrowstyle='-|>', mutation_scale=10,
                              color='#dc2626', linewidth=1.4))
ax.text(14.5, BSY + 0.18, 'trigger fires', ha='left', va='center', fontsize=8.5, color='#0f172a')
ax.add_patch(FancyArrowPatch((15.6, BSY + 0.40), (16.0, BSY + 0.40),
                              arrowstyle='-|>', mutation_scale=10,
                              color='#7c3aed', linewidth=1.4, linestyle='--'))
ax.text(16.1, BSY + 0.40, 'feedback', ha='left', va='center', fontsize=8.5, color='#0f172a')

# ============================================================================
# Save
# ============================================================================
out_png = Path(r'D:\新论文\论文\_submission\tle_architecture_v4.png')
out_pdf = out_png.with_suffix('.pdf')
fig.savefig(out_png, bbox_inches='tight', facecolor='white', dpi=300)
fig.savefig(out_pdf, bbox_inches='tight', facecolor='white')
print(f'Saved {out_png}')
print(f'Saved {out_pdf}')
plt.close()

fig_dir = Path(r'D:\新论文\实验\results\figures')
fig_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(out_png, fig_dir / 'tle_architecture_v4.png')
shutil.copy2(out_pdf, fig_dir / 'tle_architecture_v4.pdf')
print(f'Copied to {fig_dir}')
