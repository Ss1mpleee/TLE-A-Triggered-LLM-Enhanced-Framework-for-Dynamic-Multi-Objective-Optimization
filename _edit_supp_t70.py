#!/usr/bin/env python3
"""T70 round 1: supplementary_material.tex edits.

Fixes stale numbers (215, 5,156, 8 seeds, B_max=60, sec_main_v3.json,
sec_ablation_v2.json, 37h -> 22-24h).
"""
import sys
from pathlib import Path

f = Path(r'D:\新论文\论文\_submission\supplementary_material.tex')
content = f.read_text(encoding='utf-8')

edits = []

def apply(label, old, new, count=1):
    global content
    if old not in content:
        raise AssertionError(f"Edit anchor not found: {label}")
    occ = content.count(old)
    if occ < count:
        raise AssertionError(f"Edit anchor found {occ} times but {count} requested: {label}")
    content = content.replace(old, new, count)
    edits.append((label, occ, count))


# 1) L208 "the eight seeds" -> "all 30 seeds"
apply("L208 eight seeds -> 30 seeds",
      "so the eight\n          seeds all produce the same final IGD",
      "so all 30\n          seeds produce the same final IGD")

# 2) L214 "all 215 runs" -> "all 2,520 runs"
apply("L214 215 runs -> 2,520 runs",
      "The complete per-seed numeric values for all 215 runs are released in",
      "The complete per-seed numeric values for all 2,520 main runs and the 1,680 trigger-ablation + 1,260 cross-LLM extension runs (a total of 5,460 main+ablation runs across all 14 problems) are released in")

# 3) L580 B_max 60 -> 50 (main paper says 50)
apply("L580 B_max 60 -> 50",
      "UCB1 budget cap $B_{\\max}$       & 60 (30\\% of $T$) & per run \\\\",
      "UCB1 budget cap $B_{\\max}$       & 50 (25\\% of $T$) & per run \\\\")

# 4) L588 cache 5,156 -> 17,226
apply("L588 cache 5,156 -> 17,226",
      "LLM response cache               & 5{,}156 entries & SHA-256 keyed \\\\",
      "LLM response cache               & 17{,}226 entries (cross-LLM 16{,}349 + ablation 877) & SHA-256 keyed \\\\")

# 5) L215 sec_main_v3.json mention - keep (just the filename is fine)
# No change needed

# 6) L520 sec_ablation_v2.json - was 5 seeds, now 30
apply("L520 sec_ablation_v2.json fix",
      "\\texttt{results/raw/sec\\_ablation\\_v2.json} (ablation, 4 variants\n$\\times$ 2 problems $\\times$ 5 seeds)",
      "\\texttt{results/raw/sec\\_ablation\\_v2.json} (ablation, 4 variants\n$\\times$ 14 problems $\\times$ 30 seeds, total 1,680 runs)")

# 7) L309 V0/V1/V2 vs T0/T1/T2/T3 notation clarification
apply("L309 V0/V1/V2 notation clarification",
      "The V$0$/V$1$/V$2$ notation here is a 3-version budget ablation and is independent of the 4-version V$0$/V$1$/V$2$/V$3$ ablation in Table~\\ref{tab:abl} of the main manuscript and the T$0$/T$1$/T$2$/T$3$ trigger-mechanism ablation of Section~6.11",
      "The V$0$/V$1$/V$2$ notation here is a 3-version budget ablation (no LLM / heuristic budget / UCB1 bandit) and is independent of the 4-version V$0$/V$1$/V$2$/V$3$ ablation in Table~\\ref{tab:abl} of the main manuscript and the T$0$/T$1$/T$2$/T$3$ trigger-mechanism ablation of Section~6.11. The T$*$ notation is the trigger-mechanism ablation; the V$*$ notation is the budget-scheduler ablation")

# 8) L619 wall time: 37 GPU-h on RTX 4090 -> 22-24h clean
apply("L619 wall time 37 -> 22-24",
      "Expected total wall time: $\\sim 37$\\,GPU-h on an NVIDIA RTX~4090\n          (or $\\sim 12$\\,GPU-h if the cross-LLM block is skipped).",
      "Expected total wall time from a clean checkout: $\\sim 22$--$24$\\,h on an NVIDIA RTX~4090\n          (estimated from 78,500 fresh LLM calls at $\\sim$1 sec/call on local inference, plus 5,460 algorithmic runs at $\\sim$0.5 sec each), or $\\sim 1.5$--$2$\\,h when the released\n          17,226-entry LLM cache is used (the cross-LLM and ablation blocks remain fresh-LLM-call dominant; the cross-LLM block alone is $\\approx$11.4\\,h fresh).")

# 9) L611 8 GB VRAM -> keep
# 10) L617 "bash run_all.sh" --keep
# 11) L623 numerical results - keep

# 12) L208 "DE, DNSGA-II-A, and MOEA/DD" - first use of MOEA/DD full name
# Already defined in L184. Good.

# 13) Add IGD/JSON/etc first-occurrence definitions if needed
# Looking at L184 - already has comprehensive abbreviation block. Good.

# 14) L355 "n = 3 seeds" - this is the trigger sweep sensitivity, keep
# 15) L360 "n = 2--3 seeds per cell" - keep

# Save
f.write_text(content, encoding='utf-8')
print(f"supplementary_material.tex: {len(edits)} edit batches applied")
for label, occ, cnt in edits:
    print(f"  - {label}: {occ}x occurrence(s) -> replaced {cnt}x")
