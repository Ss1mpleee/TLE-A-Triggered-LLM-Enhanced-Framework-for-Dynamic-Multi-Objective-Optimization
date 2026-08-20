#!/usr/bin/env python
"""
T61 plot 2/2: 3 LLM × 14 problem IGD heatmap (cross-LLM 14 results).

Reads:  results/raw/exp6_cross_llm_n14.json (1260 rows)
Writes: results/figures/fig_cross_llm_heatmap.png + .pdf
        (also copies to paper/_submission/)

Layout: 1 heatmap, rows=3 LLMs, cols=14 problems
  - Cell value: mean IGD across 30 seeds
  - Color: log scale (lower=better=greener, higher=worse=redder)
  - Annotation: numeric value in each cell

Key findings to surface:
  - omnicoder-9b (code-specialized) underperforms on DF2 (bimodal) and DF11-DF13
  - omnicoder-9b excels on DF14 (3-objective)
  - qwen2.5 vs qwen3.5 are both competitive on 2-objective problems
"""
from __future__ import annotations
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

RAW_DIR   = REPO_ROOT / "results" / "raw"
FIG_DIR   = REPO_ROOT / "results" / "figures"
SUB_DIR   = REPO_ROOT.parent / "论文" / "_submission"
FIG_DIR.mkdir(parents=True, exist_ok=True)
SUB_DIR.mkdir(parents=True, exist_ok=True)

import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 11
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 8
sns.set_style('white')

# Load
data = json.load(open(RAW_DIR / "exp6_cross_llm_n14.json", encoding='utf-8'))
print(f'Loaded {len(data)} rows from exp6_cross_llm_n14.json')

# Group by (model, problem)
by_mp = defaultdict(list)
for r in data:
    if 'error' in r:
        continue
    by_mp[(r['model'], r['prob'])].append(r)

models = sorted({r['model'] for r in data if 'error' not in r})
# Order models: qwen2.5, qwen3.5, omnicoder (with rename for display)
DISPLAY_MODEL = {
    'qwen2.5:7b': 'qwen2.5:7b',
    'qwen3.5:9b': 'qwen3.5:9b',
    'carstenuhlig/omnicoder-9b:q8_0': 'omnicoder-9b',
}
DISPLAY_ORDER = ['qwen2.5:7b', 'qwen3.5:9b', 'carstenuhlig/omnicoder-9b:q8_0']
models_ordered = [m for m in DISPLAY_ORDER if m in models]

probs = sorted({r['prob'] for r in data if 'error' not in r},
               key=lambda x: int(x.replace('DF', '')))
print(f'Models: {models_ordered}')
print(f'Problems: {probs}')

# Build matrix: rows=models, cols=probs
mat = np.zeros((len(models_ordered), len(probs)))
counts = np.zeros_like(mat, dtype=int)
for i, m in enumerate(models_ordered):
    for j, p in enumerate(probs):
        rs = by_mp.get((m, p), [])
        if rs:
            mat[i, j] = np.mean([r['igd'] for r in rs])
            counts[i, j] = len(rs)

# Print summary
print()
print('Mean IGD matrix:')
print('  model               ' + ' '.join(f'{p:>7s}' for p in probs))
for i, m in enumerate(models_ordered):
    print(f'  {DISPLAY_MODEL[m]:<20s} ' + ' '.join(f'{mat[i,j]:>7.3f}' for j in range(len(probs))))

# Plot
fig, ax = plt.subplots(figsize=(13, 5.0))

# Use log-transformed color (IGD range is huge due to omnicoder DF10-DF13 ~1.0)
# But clamp outliers to make the rest readable
mat_log = np.log10(np.clip(mat, 1e-3, None))
# Add a small annotation-friendly version
mat_disp = mat.copy()
mat_disp[mat_disp < 1e-3] = 0.0  # treat near-zero as perfect

im = ax.imshow(mat_log, aspect='auto', cmap='RdYlGn_r', vmin=-3, vmax=1.0)

ax.set_xticks(np.arange(len(probs)))
ax.set_yticks(np.arange(len(models_ordered)))
ax.set_xticklabels(probs, rotation=0)
ax.set_yticklabels([DISPLAY_MODEL[m] for m in models_ordered])
ax.set_xlabel('CEC 2018 DMO problem')
ax.set_title('Cross-LLM IGD on 14 CEC 2018 DMO problems (n=30 each, log color scale)')

# Annotate each cell with the actual mean IGD
for i in range(len(models_ordered)):
    for j in range(len(probs)):
        v = mat[i, j]
        # Color: black on light, white on dark
        cnorm = (mat_log[i, j] - (-3)) / (1.0 - (-3))
        text_color = 'white' if cnorm < 0.3 or cnorm > 0.7 else 'black'
        # Format: 0.00 if near zero, else 3 decimals
        if v < 0.005:
            txt = '0.00'
        elif v < 0.1:
            txt = f'{v:.3f}'
        else:
            txt = f'{v:.2f}'
        ax.text(j, i, txt, ha='center', va='center', color=text_color, fontsize=8)

cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
cbar.set_label('log10(IGD) — green=good, red=bad')

# Mark special findings (with corrected understanding of the data).
# Use fig.text (figure coordinates) to place annotations below the plot
# area, where they will not overlap with the data cells. This avoids the
# fragile data-coordinate placement that previously pushed annotations
# outside the visible area.
fig.text(0.07, 0.01,
         'Key finding 1 (red):  DF2 — qwen2.5:7b has 4/30 catastrophic seeds '
         '(IGD up to 34605); conservative LLMs stay below 4.79.',
         fontsize=8.5, color='#aa0000', fontweight='bold')
fig.text(0.07, -0.04,
         'Key finding 2 (grey): DF11/DF12/DF13 (3-objective) — all three LLMs '
         'lock at IGD = 1.0 (3-objective failure floor).',
         fontsize=8.5, color='#444444')
fig.text(0.07, -0.09,
         'Key finding 3 (green): DF14 (3-objective) — qwen2.5:7b perfect 0.0 '
         'on all 30 seeds; conservative LLMs 0.003-0.005 (2 outliers each).',
         fontsize=8.5, color='#006400')

plt.tight_layout()

out = FIG_DIR / 'fig_cross_llm_heatmap.png'
plt.savefig(out, dpi=300, bbox_inches='tight')
plt.savefig(out.with_suffix('.pdf'), bbox_inches='tight')
print(f'Saved {out} + .pdf')

import shutil
for ext in ['.png', '.pdf']:
    src = FIG_DIR / f'fig_cross_llm_heatmap{ext}'
    dst = SUB_DIR / f'fig_cross_llm_heatmap{ext}'
    shutil.copy2(src, dst)
    print(f'Copied -> {dst}')

plt.close()
