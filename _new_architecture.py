#!/usr/bin/env python
"""
TLE Framework architecture figure (v3.1) — cleaned layout for SWEVO.

3-column layout:
  Left  : DMO Problem input
  Mid   : 3 layers (L3 Budget, L2 LLM Advisor, L1 DE/NSGA-II)
  Right : Triple-Signal Trigger (core contribution)

Bottom: empirical cost strip + legend.
"""
from __future__ import annotations
from pathlib import Path
import shutil
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patches as mpatches

REPO = Path(r'D:\新论文\实验\experiments')
FIG_DIR = REPO / 'results' / 'figures'
SUB = REPO.parent.parent / '论文' / '_submission'
FIG_DIR.mkdir(parents=True, exist_ok=True)
SUB.mkdir(parents=True, exist_ok=True)

# ---------- Colors (modern, print-friendly) ----------
C_PROBLEM    = '#f1f5f9'   # slate-100
C_LAYER1     = '#dbeafe'   # blue-100
C_LAYER2     = '#dcfce7'   # green-100
C_LAYER3     = '#fed7aa'   # orange-100
C_TRIGGER    = '#fef9c3'   # yellow-100
C_BOX_BR     = '#475569'   # slate-600
C_TEXT       = '#0f172a'   # slate-900
C_TEXT_MUTED = '#64748b'   # slate-500
C_ARROW_DATA = '#1e40af'   # blue-800
C_ARROW_TRIG = '#b91c1c'   # red-700
C_ARROW_FB   = '#6b21a8'   # purple-800

# ---------- Figure geometry ----------
W, H = 16, 12
DPI = 200

fig, ax = plt.subplots(figsize=(W, H), dpi=DPI)
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_aspect('equal')
ax.axis('off')
ax.add_patch(mpatches.Rectangle((0, 0), W, H, facecolor='white', zorder=0))


# ---------- Helpers ----------
def shadow_box(x, y, w, h, fc, ec=C_BOX_BR, lw=1.2, radius=0.18, z=2,
               emphasize=False, ec_w=None):
    if ec_w is None:
        ec_w = lw
    sh = FancyBboxPatch((x + 0.05, y - 0.05), w, h,
                         boxstyle=f"round,pad=0,rounding_size={radius}",
                         facecolor='#cbd5e1', alpha=0.40, edgecolor='none',
                         zorder=z - 0.1)
    ax.add_patch(sh)
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle=f"round,pad=0,rounding_size={radius}",
                         facecolor=fc, edgecolor=ec, linewidth=ec_w,
                         zorder=z)
    ax.add_patch(box)
    return box


def text(x, y, s, **kw):
    ax.text(x, y, s, zorder=10, **kw)


def arrow(p1, p2, color, lw=2.0, style='-', label=None, label_pos=None,
         label_offset=0.15, connection='arc3,rad=0', mutation=20, z=5):
    if style == '--':
        a = FancyArrowPatch(p1, p2, arrowstyle='->', mutation_scale=mutation,
                             color=color, linewidth=lw, linestyle='--',
                             connectionstyle=connection,
                             zorder=z, shrinkA=2, shrinkB=2)
    else:
        a = FancyArrowPatch(p1, p2, arrowstyle='->', mutation_scale=mutation,
                             color=color, linewidth=lw,
                             connectionstyle=connection,
                             zorder=z, shrinkA=2, shrinkB=2)
    ax.add_patch(a)
    if label is not None:
        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2
        if label_pos == 'right':   mx += label_offset
        elif label_pos == 'left': mx -= label_offset
        elif label_pos == 'top':  my += label_offset
        elif label_pos == 'bottom': my -= label_offset
        text(mx, my, label, ha='center', va='center', fontsize=10,
             color=color, style='italic',
             bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                       edgecolor=color, alpha=0.85, lw=0.6))


# ============================================================================
# Title
# ============================================================================
text(W / 2, H - 0.55, 'TLE: Triggered LLM-Enhanced Evolutionary Framework',
     ha='center', va='center', fontsize=22, fontweight='bold', color=C_TEXT)
text(W / 2, H - 1.10, 'Event-Driven LLM-EC for Dynamic Multi-Objective Optimization',
     ha='center', va='center', fontsize=14, color=C_TEXT_MUTED, style='italic')

# Decorative underline
ax.plot([W * 0.32, W * 0.68], [H - 1.45, H - 1.45], color='#0891b2',
        linewidth=2.0, zorder=2)


# ============================================================================
# Column 1: DMO Problem input (left, mid-height)
# ============================================================================
prob_x, prob_y, prob_w, prob_h = 0.4, 4.0, 3.3, 4.5
shadow_box(prob_x, prob_y, prob_w, prob_h, C_PROBLEM, ec='#64748b', lw=1.5,
           radius=0.20)
text(prob_x + prob_w / 2, prob_y + prob_h - 0.40, 'DMO Problem',
     ha='center', va='center', fontsize=15, fontweight='bold', color=C_TEXT)
text(prob_x + prob_w / 2, prob_y + 0.30, 'INPUT',
     ha='center', va='center', fontsize=9, color=C_TEXT_MUTED,
     fontweight='bold',
     bbox=dict(boxstyle='round,pad=0.18', facecolor='white',
               edgecolor=C_TEXT_MUTED, alpha=0.8, lw=0.7))

# Sub-content
info_lines = [
    ('CEC 2018 benchmark',        0.55),
    ('DF1 – DF14',                0.45),
    (r'$\tau = 10$ gens',         0.45),
    (r'($n_{\mathrm{env}} = 3$)',  0.30),
    (r'$NP = 50$, $T = 200$',      0.55),
    ('Multi-UAV: 4/8/16/32',      0.45),
    ('$n = 30$ seeds / problem',  0.30),
]
y_text = prob_y + prob_h - 1.10
for line, dy in info_lines:
    text(prob_x + prob_w / 2, y_text, line,
         ha='center', va='center', fontsize=10.5, color=C_TEXT)
    y_text -= dy


# ============================================================================
# Column 2: 3 layers stacked (center)
# ============================================================================
mid_x = 4.6
mid_w = 4.7

# Layer 3: Budget Scheduler (top of stack)
L3_y, L3_h = 7.6, 2.6
shadow_box(mid_x, L3_y, mid_w, L3_h, C_LAYER3, ec='#9a3412', lw=1.6, radius=0.20)
text(mid_x + mid_w / 2, L3_y + L3_h - 0.40,
     'Layer 3  —  Budget Scheduler',
     ha='center', va='center', fontsize=14, fontweight='bold', color='#7c2d12')
info3 = [
    ('UCB1 bandit',                          True),
    (r'$(\mathrm{per\text{-}signal},\ \mathrm{per\text{-}gen})$',  False),
    (r'$B = T/\tau$  budget rule',           True),
    (r'$\mathrm{cap} = 50$ calls / run',     False),
    ('Adaptive decision:  invoke LLM? (yes/no)', True),
]
yy = L3_y + L3_h - 0.85
for line, bold in info3:
    text(mid_x + mid_w / 2, yy, line,
         ha='center', va='center', fontsize=10.5,
         color='#7c2d12' if bold else C_TEXT_MUTED,
         fontweight='bold' if bold else 'normal',
         style='italic' if not bold else 'normal')
    yy -= 0.32

# Layer 2: LLM Advisor (middle of stack)
L2_y, L2_h = 4.5, 2.7
shadow_box(mid_x, L2_y, mid_w, L2_h, C_LAYER2, ec='#15803d', lw=1.6, radius=0.20)
text(mid_x + mid_w / 2, L2_y + L2_h - 0.40,
     'Layer 2  —  LLM Strategic Advisor',
     ha='center', va='center', fontsize=14, fontweight='bold', color='#14532d')
text(mid_x + mid_w / 2, L2_y + L2_h - 0.75,
     'Qwen-2.5-7B-Instruct via Ollama (chat-tuned, local)',
     ha='center', va='center', fontsize=10.5, color=C_TEXT)

# JSON output snippet (dark code block)
json_x = mid_x + 0.30
json_w = mid_w - 0.60
json_y = L2_y + 0.30
json_h = 1.20
ax.add_patch(FancyBboxPatch((json_x, json_y), json_w, json_h,
                              boxstyle="round,pad=0,rounding_size=0.10",
                              facecolor='#0f172a', edgecolor='#1e293b',
                              linewidth=1.0, zorder=4))
json_lines = [
    '→  JSON dual-channel output:',
    '{ "strategy": "explore",',
    '  "F": 0.65,  "CR": 0.85,',
    '  "rationale": "..." }',
]
for i, line in enumerate(json_lines):
    text(json_x + json_w / 2, json_y + json_h - 0.20 - i * 0.24,
         line, ha='center', va='center', fontsize=9.5,
         color='#e2e8f0' if i == 0 else '#a5f3fc',
         family='monospace',
         fontweight='bold' if i == 0 else 'normal')

# Layer 1: DE/NSGA-II Search Engine (bottom of stack)
L1_y, L1_h = 0.7, 3.4
shadow_box(mid_x, L1_y, mid_w, L1_h, C_LAYER1, ec='#1e40af', lw=1.6, radius=0.20)
text(mid_x + mid_w / 2, L1_y + L1_h - 0.40,
     'Layer 1  —  DE/NSGA-II Search Engine',
     ha='center', va='center', fontsize=14, fontweight='bold', color='#1e3a8a')

# Sub-pipeline (4 boxes)
sub_y = L1_y + 0.30
sub_h = 1.15
sub_box_w = 0.95
sub_centers = [mid_x + 0.65, mid_x + 1.95, mid_x + 3.20, mid_x + 4.30]
sub_labels = [
    ('Population',   r'$NP = 50$'),
    ('DE/rand/1/bin', r'$F,\ CR$ ← LLM'),
    ('Evaluate',      r'$f_1,\ f_2$'),
    ('NSGA-II',       'non-dom sort'),
]
for cx, (l1, l2) in zip(sub_centers, sub_labels):
    ax.add_patch(FancyBboxPatch((cx - sub_box_w/2, sub_y), sub_box_w, sub_h,
                                  boxstyle="round,pad=0,rounding_size=0.10",
                                  facecolor='white', edgecolor='#1e40af',
                                  linewidth=1.0, zorder=4))
    text(cx, sub_y + sub_h * 0.62, l1, ha='center', va='center',
         fontsize=9.5, fontweight='bold', color='#1e3a8a')
    text(cx, sub_y + sub_h * 0.25, l2, ha='center', va='center',
         fontsize=8.5, color=C_TEXT_MUTED, style='italic')
# Arrows between sub-pipeline boxes
for i in range(3):
    a = FancyArrowPatch((sub_centers[i] + sub_box_w/2, sub_y + sub_h/2),
                         (sub_centers[i+1] - sub_box_w/2, sub_y + sub_h/2),
                         arrowstyle='->', mutation_scale=14,
                         color=C_ARROW_DATA, linewidth=1.4, zorder=5)
    ax.add_patch(a)


# ============================================================================
# Column 3: Triple-Signal Trigger (right, full-height with strong emphasis)
# ============================================================================
T_x, T_y, T_w, T_h = 10.2, 2.7, 5.4, 7.0
shadow_box(T_x, T_y, T_w, T_h, C_TRIGGER, ec='#ca8a04', lw=2.0, ec_w=2.5,
           radius=0.20, emphasize=True)
# Header band
hdr_h = 0.95
ax.add_patch(FancyBboxPatch((T_x, T_y + T_h - hdr_h), T_w, hdr_h,
                              boxstyle="round,pad=0,rounding_size=0.20",
                              facecolor='#fde68a', edgecolor='none', zorder=3))
text(T_x + T_w / 2, T_y + T_h - 0.40, 'Triple-Signal Trigger',
     ha='center', va='center', fontsize=16, fontweight='bold', color='#713f12')
text(T_x + T_w / 2, T_y + T_h - 0.75, '(core contribution)',
     ha='center', va='center', fontsize=11, color='#713f12', style='italic')

# Three sub-signals
sig_y_top = T_y + T_h - hdr_h - 0.30
sig_h = 1.20
sig_data = [
    ('S1', 'Entropy Descent',   r'$H(P_t) < (1-\delta_H)\,H(P_{t-1})$',
     r'$\delta_H = 0.05$',         '▼', '#dc2626'),
    ('S2', 'Fitness Stagnation', r'$\Delta f < \varepsilon$ for $w$ gens',
     r'$\varepsilon = 10^{-3}$',    '–', '#0891b2'),
    ('S3', 'Environmental Change', r'$|f_t - f_{t-1}| / |f_{t-1}| > \delta_C$',
     r'$\delta_C = 0.05$',         '✱', '#7c3aed'),
]
for i, (sn, name, formula, param, icon, icon_color) in enumerate(sig_data):
    sy = sig_y_top - i * (sig_h + 0.15)
    # Icon circle
    icon_x = T_x + 0.50
    icon_y = sy - sig_h/2
    ax.add_patch(mpatches.Circle((icon_x, icon_y), 0.26,
                                  facecolor='white', edgecolor=icon_color,
                                  linewidth=2.0, zorder=5))
    text(icon_x, icon_y, icon, ha='center', va='center',
         fontsize=14, fontweight='bold', color=icon_color)
    # Text
    text(T_x + 0.95, sy - 0.18, name,
         ha='left', va='center', fontsize=12, fontweight='bold', color=C_TEXT)
    text(T_x + 0.95, sy - 0.50, formula,
         ha='left', va='center', fontsize=10, color=C_TEXT)
    # Param badge (right)
    ax.add_patch(FancyBboxPatch((T_x + T_w - 1.40, sy - 0.78), 1.20, 0.30,
                                  boxstyle="round,pad=0,rounding_size=0.05",
                                  facecolor='#fef3c7', edgecolor='#a16207',
                                  linewidth=0.7, zorder=4))
    text(T_x + T_w - 0.80, sy - 0.63, param,
         ha='center', va='center', fontsize=9, color='#713f12',
         family='monospace', fontweight='bold')

# OR bar (between S3 and the fires callout)
or_y = T_y + 0.95
ax.add_patch(FancyBboxPatch((T_x + T_w/2 - 0.45, or_y - 0.21), 0.9, 0.42,
                              boxstyle="round,pad=0,rounding_size=0.08",
                              facecolor='#fde68a', edgecolor='#b45309',
                              linewidth=1.3, zorder=4))
text(T_x + T_w/2, or_y, 'OR', ha='center', va='center',
     fontsize=13, fontweight='bold', color='#7c2d12')

# "fires" callout at bottom of trigger
fire_y = T_y + 0.40
text(T_x + T_w / 2, fire_y, '→  trigger fires',
     ha='center', va='center', fontsize=11, color='#dc2626',
     fontweight='bold',
     bbox=dict(boxstyle='round,pad=0.3', facecolor='#fef2f2',
               edgecolor='#dc2626', lw=1.3, alpha=0.95))


# ============================================================================
# Arrows (the data flow)
# ============================================================================
# 1) DMO Problem -> Layer 1 (input)
arrow((prob_x + prob_w, prob_y + prob_h * 0.5),
      (mid_x, L1_y + 0.8),
      C_ARROW_DATA, lw=2.0,
      connection='arc3,rad=-0.15')

# 2) Layer 1 -> Trigger (feedback: stats / Δf, dashed purple)
arrow((L1_x_right := mid_x + mid_w, L1_y + L1_h * 0.70),
      (T_x, T_y + 0.80),
      C_ARROW_FB, lw=1.8, style='--',
      label='stats / Δf', label_pos='right', label_offset=0.30,
      connection='arc3,rad=0.30')

# 3) Trigger -> Layer 3 (fires)
arrow((T_x, T_y + 0.80),
      (mid_x + mid_w, L3_y + 0.50),
      C_ARROW_TRIG, lw=2.2,
      label='fires', label_pos='top', label_offset=0.20,
      connection='arc3,rad=-0.30')

# 4) Layer 3 -> Layer 2 (allow?)
arrow((mid_x + mid_w * 0.70, L3_y),
      (mid_x + mid_w * 0.70, L2_y + L2_h),
      C_ARROW_DATA, lw=1.8,
      label='allow?', label_pos='right', label_offset=0.20)

# 5) Layer 2 -> Layer 1 (return F, CR, mode)
arrow((mid_x + mid_w * 0.30, L2_y),
      (mid_x + mid_w * 0.30, L1_y + L1_h),
      C_ARROW_DATA, lw=1.8, style='--',
      label=r'$F,\ CR,\ \mathrm{mode}$', label_pos='left', label_offset=0.30)


# ============================================================================
# Empirical cost strip at the very bottom
# ============================================================================
empirical_y = 0.10
empirical_h = 0.45
empirical_x = 0.4
empirical_w = W - 0.8
ax.add_patch(FancyBboxPatch((empirical_x, empirical_y), empirical_w, empirical_h,
                              boxstyle="round,pad=0,rounding_size=0.10",
                              facecolor='#f0fdf4', edgecolor='#16a34a',
                              linewidth=1.0, zorder=3))
empirical_text = (
    r'Empirical cost:  TLE  $\approx 38.6$ calls / run  '
    r'(19.3% of 200 gens, IQR 15.4–23.5%)     '
    r'Cost-norm. IGD:  $\mathbf{2.37\times}$  better than DE-LM-static  '
    r'(18.9 vs 44.9 IGD / 1000 calls)     '
    r'Multi-UAV:  19.0–21.2% task-cost reduction vs DNSGA-II-A  ($p \leq 0.0312$)'
)
text(empirical_x + empirical_w / 2, empirical_y + empirical_h / 2, empirical_text,
     ha='center', va='center', fontsize=9.5, color='#14532d')


# ============================================================================
# Legend (above empirical strip, right side)
# ============================================================================
leg_x = 11.0
leg_y = 0.75
leg_w = 4.6
leg_h = 0.85
ax.add_patch(FancyBboxPatch((leg_x, leg_y), leg_w, leg_h,
                              boxstyle="round,pad=0,rounding_size=0.10",
                              facecolor='white', edgecolor='#94a3b8',
                              linewidth=1.0, zorder=3))
text(leg_x + 0.15, leg_y + leg_h - 0.18, 'Legend:',
     ha='left', va='center', fontsize=10, fontweight='bold', color=C_TEXT)

leg_items = [
    (C_ARROW_DATA, 'data flow',         '-'),
    (C_ARROW_TRIG, 'trigger fires',     '-'),
    (C_ARROW_FB,   'feedback signal',   '--'),
]
for i, (c, label, ls) in enumerate(leg_items):
    item_y = leg_y + 0.50 - i * 0.17
    ax.add_patch(FancyArrowPatch((leg_x + 0.20, item_y),
                                  (leg_x + 0.85, item_y),
                                  arrowstyle='->', mutation_scale=12,
                                  color=c, linewidth=1.6, linestyle=ls,
                                  zorder=4))
    text(leg_x + 1.00, item_y, label, ha='left', va='center',
         fontsize=9, color=C_TEXT)


# Save
out_png = FIG_DIR / 'tle_architecture_v3.png'
out_pdf = FIG_DIR / 'tle_architecture_v3.pdf'
plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig(out_pdf, bbox_inches='tight', facecolor='white')
print(f'Saved {out_png} + {out_pdf}')
for ext in ('.png', '.pdf'):
    shutil.copy2(FIG_DIR / f'tle_architecture_v3{ext}',
                 SUB / f'tle_architecture_v3{ext}')
    print(f'Copied -> {SUB}/tle_architecture_v3{ext}')
plt.close()
