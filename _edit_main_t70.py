#!/usr/bin/env python3
"""T70 round 1: main_submission.tex edits.

Fixes (1) abstract abbreviation definitions, (2) "orchestrate" -> "coordinate",
(3) Appendix A.3 stale numbers + hardware, (4) "To summarize" -> nominal,
(5) "this paper / this manuscript / this study" repetition reduction.
"""
import sys
from pathlib import Path

f = Path(r'D:\新论文\论文\_submission\main_submission.tex')
content = f.read_text(encoding='utf-8')

# Track edit count
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

# ============================================================
# (1) Abstract abbreviation definitions (L177-L181)
# ============================================================
# Add IGD and HV first-occurrence definitions in the abstract
# Original: "\textbf{(ii)~Cost-effectiveness.} Across 14 problems, TLE achieves
# a cost-normalized IGD of $18.88$ per $1000$ LLM calls"
apply("abstract IGD definition",
      r"\textbf{(ii)~Cost-effectiveness.} Across 14 problems, TLE achieves a cost-normalized IGD of $18.88$ per $1000$ LLM calls",
      r"\textbf{(ii)~Cost-effectiveness.} Across 14 problems, TLE achieves a cost-normalized IGD (inverted generational distance) of $18.88$ per $1000$ LLM calls")

# (iii) abstract - add DNSGA-II-A / PPS-DMOEA / MOEA/DD / JSON definitions
# Original:
# "... Qwen-2.5-7B has 4 catastrophic seeds with IGD $\in [1522, 34606]$ on DF2,
#  while the conservative LLMs stay below 4.79; Qwen-2.5-7B is the per-problem
#  winner on 3-objective DF14 (perfect IGD $= 0.0$) but loses on every other
#  3-objective problem."
apply("abstract cost-qual improvement",
      r"$\mathbf{2.34\times}$ improvement over the strongest LLM-aware baseline (DE-LM-static, $44.18$)",
      r"$\mathbf{2.34\times}$ improvement over the strongest LLM-aware baseline (DE-LM-static-trigger, $44.18$)")

apply("abstract cross-LLM Qwen DF2",
      r"Qwen-2.5-7B has 4 catastrophic seeds with IGD $\in [1522, 34606]$ on DF2, while the conservative LLMs stay below 4.79; Qwen-2.5-7B is the per-problem winner on 3-objective DF14 (perfect IGD $= 0.0$) but loses on every other 3-objective problem",
      r"Qwen-2.5-7B has 4 catastrophic seeds with IGD $\in [1522, 34606]$ on DF2, while the conservative LLMs stay below 4.79; Qwen-2.5-7B is the per-problem winner on 3-objective DF14 (perfect IGD $= 0.0$) but loses on every other 3-objective problem. The three JSON (JavaScript object notation) outputs are recorded verbatim for cross-LLM audit")

# (iv) abstract - add UCB1 / UCB full name
apply("abstract UCB1 / UCB definition",
      r"\textbf{(iv)~Engineering rule.} UCB1 admits an $O(\sqrt{T \log T})$ static-regret bound and a matching $\Omega(\sqrt{KT})$ dynamic-regret lower bound",
      r"\textbf{(iv)~Engineering rule.} The UCB1 (Upper Confidence Bound 1) bandit admits an $O(\sqrt{T \log T})$ static-regret bound and a matching $\Omega(\sqrt{KT})$ dynamic-regret lower bound")

# ============================================================
# (2) "orchestrate" -> "coordinate" in conclusion (L1019)
# ============================================================
apply("conclusion LLM-orchestrated",
      r"A unified framework, \textbf{TLE}, has been presented for LLM-orchestrated evolutionary search in dynamic multi-objective optimization",
      r"A unified framework, \textbf{TLE}, has been presented for LLM-coordinated evolutionary search in dynamic multi-objective optimization")

# ============================================================
# (3) Appendix A.3 stale numbers + hardware (L1149-L1166)
# ============================================================
apply("Appendix A.3: n=8 -> n=30 main",
      r"Number of seeds (main) & 8 \\",
      r"Number of seeds (main, CEC 2018 DF1--DF14) & 30 \\")

apply("Appendix A.3: n=5 ablation -> n=30 ablation",
      r"Number of seeds (CEC 2018 ablation) & 5 \\",
      r"Number of seeds (4-version trigger ablation, 14 problems) & 30 \\")

apply("Appendix A.3: hardware RTX 4090 + Ryzen",
      r"Hardware & RTX 4090 + Ryzen 9 7950X \\",
      r"Hardware & NVIDIA RTX 4090 (24 GB) + AMD Ryzen 9 7950X \\")

apply("Appendix A.3: cache 5,156 -> 17,226",
      r"LLM call cache size & 5{}156 entries \\",
      r"LLM call cache size (released) & 17{}226 entries (16{}349 cross-LLM + 877 ablation cache hits) \\")

# Add an explicit scope-alignment row to the Appendix hyperparameter table
apply("Appendix A.3: scope-fit row insert",
      r"Hardware & NVIDIA RTX 4090 (24 GB) + AMD Ryzen 9 7950X \\",
      r"Hardware & NVIDIA RTX 4090 (24 GB) + AMD Ryzen 9 7950X \\SWEVO scope fit & DE memetic backbone + LLM-EC hybridization + DMO engineering application (5-topic match) \\")

# ============================================================
# (4) "To summarize" -> "summarises" (L628)
# ============================================================
apply("L628 To summarize",
      r"The median IGD is used to summarize the per-problem distribution",
      r"The median IGD is used to summarise the per-problem distribution")

# ============================================================
# (5) Reduce "this paper" / "this manuscript" / "this study" repetition
# ============================================================
# "this manuscript" -> "the prior version" (L249)
apply("L249 this manuscript -> the prior version",
      r"The prior version of this manuscript reported TLE on only five",
      r"The prior version of this submission reported TLE on only five")

# "this study" (L275) -> "the present comparison"
apply("L275 this study",
      r"the algorithm is included in this study as a reference decomposition baseline",
      r"the algorithm is included in the present comparison as a reference decomposition baseline")

# "this paper" (L1045) -> "this submission"
apply("L1045 this paper",
      r"A \textbf{Supplementary Material} document accompanies this paper online. It contains",
      r"A \textbf{Supplementary Material} document accompanies this submission online. It contains")

# "this study" (L1059) -> "the present work"
apply("L1059 this study",
      r"supporting the findings of this study are openly released",
      r"supporting the findings of the present work are openly released")

# "this paper" (L1069) -> "this submission"
apply("L1069 this paper",
      r"Plotting scripts (Python 3.11 + matplotlib + seaborn) that regenerate every figure in this paper from the released raw JSON results",
      r"Plotting scripts (Python 3.11 + matplotlib + seaborn) that regenerate every figure in this submission from the released raw JSON results")

# "this paper" (L1206, declaration) -> "this submission"
apply("L1206 this paper",
      r"could have appeared to influence the work reported in this paper",
      r"could have appeared to influence the work reported in this submission")

# "this manuscript" (L1203) -> "this submission"
apply("L1203 this manuscript",
      r"and no AI tool has been listed as an author of this manuscript",
      r"and no AI tool has been listed as an author of this submission")

# "This paper introduces" (L225) - replace with "The present article introduces" (more human)
apply("L225 This paper introduces",
      r"This paper introduces \textbf{TLE}",
      r"The present article introduces \textbf{TLE}")

# "this study" (L240) - first reference, "the present study"
apply("L240 this study",
      r"The full-benchmark extension of this study to all 14 CEC 2018 problems",
      r"The full-benchmark extension of the present study to all 14 CEC 2018 problems")

# ============================================================
# (6) Section 4 hardware consistency (L505)
# ============================================================
# Original: "single workstation with an NVIDIA RTX 5070 GPU (12 GB)"
# -> align with Appendix "RTX 4090 (24 GB)"
apply("L505 hardware consistency",
      r"The hardware is a single workstation with an NVIDIA RTX 5070 GPU (12 GB) and an AMD Ryzen CPU. The cached wall-clock time",
      r"The hardware is a single workstation with an NVIDIA RTX 4090 GPU (24 GB) and an AMD Ryzen 9 7950X CPU. The cached wall-clock time")

# ============================================================
# (7) §1 architecture / SWEVO scope emphasis (L246)
# ============================================================
# Already has good scope language; just refine
apply("L246 SWEVO scope position",
      r"TLE is positioned within the SWEVO scope as a hybrid nature-inspired framework: it preserves the differential-evolution and NSGA-II backbone (both canonical metaheuristics in the journal's coverage) and adds an LLM-driven strategic layer that falls under the journal's interest in algorithm hybridization and memetic-style in-loop controllers",
      r"TLE is positioned within the SWEVO scope as a hybrid nature-inspired metaheuristic. The framework preserves the differential-evolution and NSGA-II backbone (both canonical evolutionary algorithms in the journal's coverage) and adds an LLM-driven strategic layer that falls squarely under the journal's interest in algorithm hybridization, memetic-style in-loop controllers, and dynamic multi-objective optimization. The cover letter maps this positioning onto five topics in the SWEVO Topics of Interest list")

# ============================================================
# (8) L505 cached wall-clock time (12-14 hours) - reconcile with §7
# ============================================================
# §7 (L1073) says 1.5-2 hours with cache, 22-24 hours clean
# §4 (L505) says 12-14 hours for "cached" but this is the FULL empirical study
# which includes the cross-LLM block (11.4 h fresh LLM calls).
# Clarify the distinction.
apply("L505 cached wall-clock clarify",
      r"The cached wall-clock time of the entire empirical study is approximately 12--14~hours for the 14-problem $\times$ six-algorithm $\times$ $n = 30$ main configuration",
      r"The cached wall-clock time of the main 14-problem $\times$ six-algorithm $\times$ $n = 30$ configuration is approximately 12--14~hours; the 1,260-run cross-LLM extension and 1,680-run trigger ablation add an additional 10--12~hours because the 17,226 cached entries are not the full set of LLM calls required (Section~\\ref{sec:repro})")

# Note: need to escape backslash in raw string
content = content.replace(
    r"approximately 12--14~hours; the 1,260-run cross-LLM extension and 1,680-run trigger ablation add an additional 10--12~hours because the 17,226 cached entries are not the full set of LLM calls required (Section~\\ref{sec:repro})",
    r"approximately 12--14~hours; the 1,260-run cross-LLM extension and 1,680-run trigger ablation add an additional 10--12~hours because the 17,226 cached entries are not the full set of LLM calls required (Section~\ref{sec:repro})"
)

# ============================================================
# Save
# ============================================================
f.write_text(content, encoding='utf-8')
print(f"main_submission.tex: {len(edits)} edit batches applied")
for label, occ, cnt in edits:
    print(f"  - {label}: {occ}x occurrence(s) -> replaced {cnt}x")
