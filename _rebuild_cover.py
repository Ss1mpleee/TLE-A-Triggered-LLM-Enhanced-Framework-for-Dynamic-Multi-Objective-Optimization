# -*- coding: utf-8 -*-
"""
cover_letter.tex was mangled by an earlier PowerShell session that ate
the $ inside double-quoted strings.  Strategy: rebuild the corrupted
long-paragraph (line 33) by re-inserting the missing $ and
re-expanding the V$x$ placeholders.
"""
import re

PATH = r"D:\新论文\论文\_submission\cover_letter.tex"

with open(PATH, "r", encoding="utf-8") as f:
    raw = f.read()

# Replace the broken innovation paragraph with a clean one.
# The "old" mangled text was:
# "...adjustment of the differential-evolution scaling factor $ and crossover rate $..."
# "$\\sqrt{T \\log T}$$ regret bound..."
# "$\\Omega(\\sqrt{KT})$$ for the non-stationary..."
# "$\\mathbf{B} \\geq T/\\tau$$ for sizing..."
# "$n = 30$$ seeds per problem..."
# "$4 \\times 14 \\times 30 = 1680$$-run trigger-mechanism ablation (V$ always, V$ entropy, V$ entropy+stagnation, V$ triple-signal + bandit)..."
# "$3 \\times 14 \\times 30 = 1260$$-run cross-LLM extension..."

# I'll surgically replace the whole long sentence.
old_sentence = (
    "TLE replaces the periodic LLM call with an event-driven "
    "\\emph{triple-signal trigger} (population-entropy descent, "
    "fitness stagnation, environmental change) that fires the LLM "
    "only when intervention is likely beneficial, paired with a "
    "\\emph{dual-channel mapping} that converts natural-language "
    "recommendations into both a strategic decision (operator mode, "
    "search focus) and a continuous adjustment of the "
    "differential-evolution scaling factor \\$ and crossover rate \\$, "
    "and with a \\emph{UCB1 bandit budget scheduler} with a stationary "
    "\\\$O(\\\\sqrt{T \\\\log T})\\\$ regret bound and a matching "
    "dynamic-regret lower bound of \\\$\\\\Omega(\\\\sqrt{KT})\\\\$ for "
    "the non-stationary DMO regime. The analysis yields the practical "
    "rule of thumb \\\\$\\\\mathbf{B} \\\\geq T/\\\\tau\\\\$ for sizing "
    "the LLM budget in real DMO deployment. On the full CEC~2018 dynamic "
    "benchmark suite (all 14 problems DF1--DF14, including the 3-objective "
    "DF9--DF14, six algorithms, \\\\$n = 30\\\\$ seeds per problem), TLE "
    "is statistically competitive with the strongest classical baseline "
    "(Friedman rank 4.36 of 6, within the Nemenyi CD bar of DNSGA-II-A, "
    "DE, PPS-DMOEA, and DE-LM-static-trigger) and is the cost-effective "
    "frontier among LLM-aware algorithms: TLE achieves a cost-normalized "
    "IGD of 18.9 (IGD per 1000 LLM calls), "
    "\\\\mathbf{2.37\\\\times} better than the DE-LM-static-trigger "
    "baseline (44.9), even though TLE spends more LLM calls per run on "
    "average (38.6 vs.\\\\ 16.6). The revision adds two large-scale "
    "ablation studies that strengthen the empirical evidence: a "
    "\\\\ \\\\times 14 \\\\times 30 = 1680\\\\$-run trigger-mechanism "
    "ablation (V\\\\$ always, V\\\\$ entropy, V\\\\$ entropy+stagnation, "
    "V\\\\$ triple-signal + bandit) and a "
    "\\\\ \\\\times 14 \\\\times 30 = 1260\\\\$-run cross-LLM extension "
    "to the full 14-problem benchmark suite (replacing the original "
    "3-problem pilot). The trigger ablation returns Friedman "
    "\\\\chi\\\\textasciicircum{}2 = 4.939, p = 0.176 "
    "(\\\\mathrm{CD} = 1.254 for"
)

# The replacement (CLEAN LaTeX with proper $...$ math and T$x$ notation)
new_sentence = (
    "TLE replaces the periodic LLM call with an event-driven "
    "\\emph{triple-signal trigger} (population-entropy descent, "
    "fitness stagnation, environmental change) that fires the LLM "
    "only when intervention is likely beneficial, paired with a "
    "\\emph{dual-channel mapping} that converts natural-language "
    "recommendations into both a strategic decision (operator mode, "
    "search focus) and a continuous adjustment of the "
    "differential-evolution scaling factor $F$ and crossover rate $CR$, "
    "and with a \\emph{UCB1 bandit budget scheduler} with a stationary "
    "$O(\\sqrt{T \\log T})$ regret bound and a matching "
    "dynamic-regret lower bound of $\\Omega(\\sqrt{KT})$ for "
    "the non-stationary DMO regime. The analysis yields the practical "
    "rule of thumb $\\mathbf{B} \\geq T/\\tau$ for sizing "
    "the LLM budget in real DMO deployment. On the full CEC~2018 dynamic "
    "benchmark suite (all 14 problems DF1--DF14, including the 3-objective "
    "DF9--DF14, six algorithms, $n = 30$ seeds per problem), TLE "
    "is statistically competitive with the strongest classical baseline "
    "(Friedman rank 4.36 of 6, within the Nemenyi CD bar of DNSGA-II-A, "
    "DE, PPS-DMOEA, and DE-LM-static-trigger) and is the cost-effective "
    "frontier among LLM-aware algorithms: TLE achieves a cost-normalized "
    "IGD of 18.9 (IGD per 1000 LLM calls), "
    "$\\mathbf{2.37\\times}$ better than the DE-LM-static-trigger "
    "baseline (44.9), even though TLE spends more LLM calls per run on "
    "average (38.6 vs.\\ 16.6). The revision adds two large-scale "
    "ablation studies that strengthen the empirical evidence: a "
    "$4 \\times 14 \\times 30 = 1680$-run trigger-mechanism "
    "ablation (T$0$ always, T$1$ entropy, T$2$ entropy+stagnation, "
    "T$3$ triple-signal + bandit) and a "
    "$3 \\times 14 \\times 30 = 1260$-run cross-LLM extension "
    "to the full 14-problem benchmark suite (replacing the original "
    "3-problem pilot). The trigger ablation returns Friedman "
    "$\\chi^2 = 4.939, p = 0.176$ ($\\mathrm{CD} = 1.254$ for"
)

if old_sentence in raw:
    new_raw = raw.replace(old_sentence, new_sentence)
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(new_raw)
    print(f"[cover-fix] old sentence replaced ({len(old_sentence)} chars)")
else:
    print("[cover-fix] old sentence not found verbatim, attempting fuzzy")
    # Find the start of the broken sentence and replace forward
    start_marker = "TLE replaces the periodic LLM call"
    idx = raw.find(start_marker)
    if idx == -1:
        print("[cover-fix] start_marker not found; aborting")
    else:
        # Find end: look for "(\\mathrm{CD} = 1.254 for"
        end_marker = "(\\mathrm{CD} = 1.254 for"
        # But the broken version has \\mathrm so search for that
        end_marker_broken = "(\\\\mathrm{CD} = 1.254 for"
        end_idx = raw.find(end_marker_broken, idx)
        if end_idx == -1:
            end_idx = raw.find(end_marker, idx)
        if end_idx == -1:
            print("[cover-fix] end_marker not found; aborting")
        else:
            print(f"[cover-fix] span {idx}..{end_idx} ({end_idx-idx} chars)")
            new_raw = raw[:idx] + new_sentence + raw[end_idx + len(end_marker_broken):]
            with open(PATH, "w", encoding="utf-8") as f:
                f.write(new_raw)
            print(f"[cover-fix] sentence replaced (fuzzy mode)")
