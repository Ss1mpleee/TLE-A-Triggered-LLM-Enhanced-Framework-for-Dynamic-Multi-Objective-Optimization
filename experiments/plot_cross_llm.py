#!/usr/bin/env python
"""
TLE-DMO reproduction script.

The four lines below make this script runnable from any working directory:
it puts the repository root on `sys.path` and exposes the standard result
directories as module-level `Path` constants.  Do not delete them.
"""
from __future__ import annotations
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

RAW_DIR   = REPO_ROOT / "results" / "raw"
FIG_DIR   = REPO_ROOT / "results" / "figures"
CACHE_DIR = REPO_ROOT / "results" / "llm_cache"

"""Plot cross-LLM comparison from exp6_cross_llm.json.

Shows: for each (model, problem), mean IGD with std error bars.
Also shows: LLM invocation count per model.

Notable: qwen3.5:9b and omnicoder-9b produce byte-identical IGD and
invocation counts across all 6 runs (both default to explore/F=0.5/CR=0.9),
so their lines/markers overlap on the right subplot. We use distinct
markers (○ / □ / △) to make the overlap visible to the reader, and add
a caption annotation explaining the equivalence.
"""
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
from pathlib import Path

# Set academic style
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['legend.fontsize'] = 9
sns.set_style('whitegrid')

data = json.load(open(RAW_DIR / "exp6_cross_llm.json", encoding='utf-8'))
by_mp = defaultdict(list)
for r in data:
    by_mp[(r['model'], r['prob'])].append(r)

models = sorted({r['model'] for r in data})
probs = ['DF1', 'DF5', 'DF7']
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

# Subplot 1: IGD per (model, problem)
ax = axes[0]
x = np.arange(len(probs))
w = 0.27
colors = {'qwen2.5:7b': '#D55E00',
          'qwen3.5:9b': '#56B4E9',
          'carstenuhlig/omnicoder-9b:q8_0': '#999999'}
labels = {'qwen2.5:7b': 'qwen2.5:7b (aggressive)',
          'qwen3.5:9b': 'qwen3.5:9b (conservative)',
          'carstenuhlig/omnicoder-9b:q8_0': 'omnicoder-9b (conservative)'}
# Distinct hatch patterns to differentiate the two conservative models
hatches = {'qwen2.5:7b': '',
           'qwen3.5:9b': '',
           'carstenuhlig/omnicoder-9b:q8_0': '..'}
for i, m in enumerate(models):
    igds = []
    stds = []
    for p in probs:
        rs = by_mp.get((m, p), [])
        if rs:
            igds.append(np.mean([r['igd'] for r in rs]))
            stds.append(np.std([r['igd'] for r in rs]))
        else:
            igds.append(0)
            stds.append(0)
    ax.bar(x + (i - 1) * w, igds, w, yerr=stds, label=labels[m],
           color=colors[m], capsize=4, edgecolor='black', linewidth=0.5,
           hatch=hatches[m])
ax.set_xticks(x)
ax.set_xticklabels(probs)
ax.set_xlabel('CEC 2018 DMO problem')
ax.set_ylabel('IGD (lower is better, log scale)')
ax.set_yscale('log')
ax.set_title('Cross-LLM IGD (TLE, 2 seeds, 200 generations)')
ax.legend(loc='upper left')
ax.grid(axis='y', alpha=0.3)

# Subplot 2: LLM invocation count — use distinct markers so overlapping
# qwen3.5 / omnicoder lines remain visible.  Both models produce
# byte-identical invocations (14/20, 4/6, 15/17), so we slightly
# offset omnicoder's x positions to make its diamond markers visible.
ax = axes[1]
marker_map = {'qwen2.5:7b': 'o',
              'qwen3.5:9b': 's',
              'carstenuhlig/omnicoder-9b:q8_0': 'D'}  # diamond for omnicoder
marker_size_map = {'qwen2.5:7b': 11,
                   'qwen3.5:9b': 10,
                   'carstenuhlig/omnicoder-9b:q8_0': 10}
x_offset = {'qwen2.5:7b': 0.0,
            'qwen3.5:9b': -0.08,
            'carstenuhlig/omnicoder-9b:q8_0': 0.08}  # small x offset
x_idx = np.arange(len(probs))
for m in models:
    invs = []
    for p in probs:
        rs = by_mp.get((m, p), [])
        if rs:
            invs.append(np.mean([r['invocations'] for r in rs]))
        else:
            invs.append(0)
    # Draw qwen3.5 first (lower zorder), then omnicoder on top
    zorder = 2 if m == 'carstenuhlig/omnicoder-9b:q8_0' else 3
    ax.plot(x_idx + x_offset[m], invs,
            marker=marker_map[m], markersize=marker_size_map[m],
            linestyle='-' if m == 'qwen2.5:7b' else '--',
            linewidth=1.8,
            label=labels[m], color=colors[m],
            markeredgecolor='black', markeredgewidth=1.0,
            zorder=zorder)
ax.set_xticks(x_idx)
ax.set_xticklabels(probs)
ax.set_xlabel('CEC 2018 DMO problem')
ax.set_ylabel('LLM invocations (mean, 2 seeds)')
ax.set_title('LLM invocation rate per model\n(qwen3.5 and omnicoder-9b give byte-identical results, dashed vs dotted)')
ax.legend(loc='upper right', fontsize=8)
ax.grid(True, alpha=0.3)
ax.set_ylim(bottom=0)

plt.tight_layout()
out = FIG_DIR / "fig_cross_llm.png"
plt.savefig(out, dpi=300, bbox_inches='tight')
plt.savefig(out.with_suffix('.pdf'), bbox_inches='tight')
print(f'Saved {out} + .pdf')
