# -*- coding: utf-8 -*-
"""
Second pass: cover remaining V$x$ / V0 / V1 / V2 / V3 variants in
plot scripts.  Only touches DISPLAY text, LaTeX output strings, and
human-readable comments — never the JSON KEY names ('V0_baseline' etc.)
and never the variable names (VERSIONS list etc.).
"""
import re

DOLLAR = chr(36)

FILES = [
    r"D:\新论文\实验\experiments\plot_ablation_lite.py",
    r"D:\新论文\实验\experiments\plot_outliers_and_invocations.py",
    r"D:\新论文\实验\experiments\stats_ablation_crossllm.py",
]

# Use a tighter rule: only swap V$x$ when it's in display/label context.
# Detect with: preceded by quote ' "  ( [ : space-after-colon  OR  surrounded by $...$
# Simpler: do a context-sensitive substitution line-by-line, swapping only
# inside string literals and inside comment lines that contain a single V$x$
# reference (not the JSON KEY list).

import ast, tokenize, io


def is_key_ref(line: str) -> bool:
    """True if the line is referencing a JSON KEY like 'V0_baseline'."""
    return bool(re.search(r"'V[0-3]_(baseline|single|double|triple)'", line))


def transform_line(line: str) -> str:
    """Within one line, swap V$x$ (or (Vx) display) to T$x$ only when
    the line is NOT a key-reference line.
    """
    if is_key_ref(line):
        return line

    s = line

    # "V0/V1/V2/V3" / "V0/V1/V2" / "V1/V2/V3"
    s = re.sub(r"\bV0/V1/V2/V3\b", "T" + DOLLAR + "0" + DOLLAR + "/T" + DOLLAR + "1" + DOLLAR + "/T" + DOLLAR + "2" + DOLLAR + "/T" + DOLLAR + "3" + DOLLAR, s)
    s = re.sub(r"\bV1/V2/V3\b",   "T" + DOLLAR + "1" + DOLLAR + "/T" + DOLLAR + "2" + DOLLAR + "/T" + DOLLAR + "3" + DOLLAR, s)
    s = re.sub(r"\bV0/V1/V2\b",   "T" + DOLLAR + "0" + DOLLAR + "/T" + DOLLAR + "1" + DOLLAR + "/T" + DOLLAR + "2" + DOLLAR, s)

    # "V0, V1, V2, V3"  in strings
    s = re.sub(r"\bV0, V1, V2, V3\b", "T" + DOLLAR + "0" + DOLLAR + ", T" + DOLLAR + "1" + DOLLAR + ", T" + DOLLAR + "2" + DOLLAR + ", T" + DOLLAR + "3" + DOLLAR, s)
    s = re.sub(r"\bV0, V1, V2\b",     "T" + DOLLAR + "0" + DOLLAR + ", T" + DOLLAR + "1" + DOLLAR + ", T" + DOLLAR + "2" + DOLLAR, s)

    # "vs V0, " / "vs V1, " / "vs V2"  in summary strings
    s = re.sub(r" vs V0,",  " vs T" + DOLLAR + "0" + DOLLAR + ",", s)
    s = re.sub(r" vs V1,",  " vs T" + DOLLAR + "1" + DOLLAR + ",", s)
    s = re.sub(r" vs V2\b", " vs T" + DOLLAR + "2" + DOLLAR, s)

    # "V3 vs V0" / "V3 vs V1" / "V3 vs V2" inside display strings
    s = re.sub(r"\bV3 vs V0\b", "T" + DOLLAR + "3" + DOLLAR + " vs T" + DOLLAR + "0" + DOLLAR, s)
    s = re.sub(r"\bV3 vs V1\b", "T" + DOLLAR + "3" + DOLLAR + " vs T" + DOLLAR + "1" + DOLLAR, s)
    s = re.sub(r"\bV3 vs V2\b", "T" + DOLLAR + "3" + DOLLAR + " vs T" + DOLLAR + "2" + DOLLAR, s)

    # "V3 > V0" etc.
    s = re.sub(r"\bV3 > V0\b", "T" + DOLLAR + "3" + DOLLAR + " > T" + DOLLAR + "0" + DOLLAR, s)
    s = re.sub(r"\bV3 > V1\b", "T" + DOLLAR + "3" + DOLLAR + " > T" + DOLLAR + "1" + DOLLAR, s)
    s = re.sub(r"\bV3 > V2\b", "T" + DOLLAR + "3" + DOLLAR + " > T" + DOLLAR + "2" + DOLLAR, s)

    # "V1 < V3"
    s = re.sub(r"\bV1 < V3\b", "T" + DOLLAR + "1" + DOLLAR + " < T" + DOLLAR + "3" + DOLLAR, s)
    s = re.sub(r"\bV1 $<$ V3\b", "T" + DOLLAR + "1" + DOLLAR + " $<$ T" + DOLLAR + "3" + DOLLAR, s)

    # "(V1) ..." / "(V2) ..."  parenthetical references in narrative
    s = re.sub(r"\(V1\)\b", "(T" + DOLLAR + "1" + DOLLAR + ")", s)
    s = re.sub(r"\(V2\)\b", "(T" + DOLLAR + "2" + DOLLAR + ")", s)
    s = re.sub(r"\(V3\)\b", "(T" + DOLLAR + "3" + DOLLAR + ")", s)
    s = re.sub(r"\(V0\)\b", "(T" + DOLLAR + "0" + DOLLAR + ")", s)

    # In a comment: "V0 (always-trigger, cap=50)" etc.
    s = re.sub(r"\bV0 \(always-trigger, cap=50\)", "T" + DOLLAR + "0" + DOLLAR + " (always-trigger, cap=50)", s)
    s = re.sub(r"\bV1 \(single entropy\)",          "T" + DOLLAR + "1" + DOLLAR + " (single entropy)", s)
    s = re.sub(r"\bV2 \(double entropy\+stagnation\)", "T" + DOLLAR + "2" + DOLLAR + " (double entropy+stagnation)", s)
    s = re.sub(r"\bV3 \(triple\) is the proposed method", "T" + DOLLAR + "3" + DOLLAR + " (triple) is the proposed method", s)

    # In a comment: V0 "wins" / V3 dominates
    s = re.sub(r'\bV0 "wins" on', 'T' + DOLLAR + '0' + DOLLAR + ' "wins" on', s)
    s = re.sub(r"\bV3 dominates on", "T" + DOLLAR + "3" + DOLLAR + " dominates on", s)

    # In set_title or string: "Trigger sparsity: V1/V2/V3 reduce invocations vs V0"
    s = re.sub(r"V1/V2/V3 reduce invocations vs V0", "T" + DOLLAR + "1" + DOLLAR + "/T" + DOLLAR + "2" + DOLLAR + "/T" + DOLLAR + "3" + DOLLAR + " reduce invocations vs T" + DOLLAR + "0" + DOLLAR, s)

    # In strings: "V0 (always)" / "V1 (entropy)" / "V2 (entr+stag)" / "V3 (proposed)"
    s = re.sub(r"'V0 \(always\)\b",   "'T" + DOLLAR + "0" + DOLLAR + " (always)'", s)
    s = re.sub(r"'V1 \(entropy\)\b",  "'T" + DOLLAR + "1" + DOLLAR + " (entropy)'", s)
    s = re.sub(r"'V2 \(entr\+stag\)\b", "'T" + DOLLAR + "2" + DOLLAR + " (entr+stag)'", s)
    s = re.sub(r"'V3 \(proposed\)\b", "'T" + DOLLAR + "3" + DOLLAR + " (proposed)'", s)

    # V2 (entropy+stagnation)  in VERSION_LABELS dict
    s = re.sub(r"'V2 \(entropy\+stagnation\)\b", "'T" + DOLLAR + "2" + DOLLAR + " (entropy+stagnation)'", s)

    # "V3 (proposed: triple)"  variant
    s = re.sub(r"'V3 \(proposed: triple\)\b", "'T" + DOLLAR + "3" + DOLLAR + " (proposed: triple)'", s)

    # "V1 loses to V0" / "V1 < V0"  in narrative
    s = re.sub(r"\bV1 loses to V0\b", "T" + DOLLAR + "1" + DOLLAR + " loses to T" + DOLLAR + "0" + DOLLAR, s)

    # generic "V0 ... V1 ... V2 ... V3 ..." inline narratives (catch-all ONLY
    # in non-key lines — we already filter is_key_ref at top)
    # 4-version  (V0 always, V1 entropy-only, V2 entropy+stagnation, V3 triple-signal + UCB1 bandit)
    s = re.sub(r"\bV0 always, V1 entropy-only, V2 entropy\+stagnation, V3 triple-signal",
               "T" + DOLLAR + "0" + DOLLAR + " always, T" + DOLLAR + "1" + DOLLAR + " entropy-only, T" + DOLLAR + "2" + DOLLAR + " entropy+stagnation, T" + DOLLAR + "3" + DOLLAR + " triple-signal", s)
    s = re.sub(r"\bV0 always, V1 entropy, V2 entropy\+stagnation, V3 triple-signal",
               "T" + DOLLAR + "0" + DOLLAR + " always, T" + DOLLAR + "1" + DOLLAR + " entropy, T" + DOLLAR + "2" + DOLLAR + " entropy+stagnation, T" + DOLLAR + "3" + DOLLAR + " triple-signal", s)

    return s


for path in FILES:
    with open(path, "r", encoding="utf-8") as f:
        s = f.read()
    new_lines = [transform_line(l) for l in s.split("\n")]
    new_s = "\n".join(new_lines)
    if new_s != s:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_s)
        # count diff
        diff_count = sum(1 for a, b in zip(s.split("\n"), new_s.split("\n")) if a != b)
        print(f"[patched2] {path}  ({diff_count} line(s) changed)")
    else:
        print(f"[no change2] {path}")
