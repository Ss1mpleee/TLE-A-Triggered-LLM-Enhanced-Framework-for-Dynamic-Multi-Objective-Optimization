# -*- coding: utf-8 -*-
"""
Update 3 plot/stats scripts to use T$x$ labels in DISPLAY text and in
LaTeX output strings, while keeping the JSON KEY names ('V0_baseline',
'V1_single', etc.) intact so the cached experimental data is still
readable.
"""
import re
import sys

DOLLAR = chr(36)  # '$'

FILES = [
    r"D:\新论文\实验\experiments\plot_ablation_lite.py",
    r"D:\新论文\实验\experiments\plot_outliers_and_invocations.py",
    r"D:\新论文\实验\experiments\stats_ablation_crossllm.py",
]


# Match V$x$ in display/LaTeX string contexts but NOT inside KEY names
# like 'V0_baseline'.  We do this by requiring either $...$ or surrounded
# by non-alnum/underscore.
PATTERNS = [
    # "V0 (always" / "V1 (entropy" / "V2 (entr+stag)" / "V3 (proposed" labels
    (re.compile(r"'V0 \(always[^']*'"),        "'T" + DOLLAR + "0" + DOLLAR + " (always, cap=50)'"),
    (re.compile(r"'V1 \(entropy[^']*'"),       "'T" + DOLLAR + "1" + DOLLAR + " (entropy only)'"),
    (re.compile(r"'V2 \(entr\+stag[^']*'"),    "'T" + DOLLAR + "2" + DOLLAR + " (entropy+stagnation)'"),
    (re.compile(r"'V3 \(proposed[^']*'"),      "'T" + DOLLAR + "3" + DOLLAR + " (proposed: triple)'"),

    # "V3 wins (sig.):" / "V3 vs V0..." / "V3 vs V1" / "V3 vs V2"  in prints
    (re.compile(r'\bV3 vs V0\b'),              "T" + DOLLAR + "3" + DOLLAR + " vs T" + DOLLAR + "0" + DOLLAR),
    (re.compile(r'\bV3 vs V1\b'),              "T" + DOLLAR + "3" + DOLLAR + " vs T" + DOLLAR + "1" + DOLLAR),
    (re.compile(r'\bV3 vs V2\b'),              "T" + DOLLAR + "3" + DOLLAR + " vs T" + DOLLAR + "2" + DOLLAR),
    (re.compile(r'\bV0, V1, V2, V3\b'),       "T" + DOLLAR + "0" + DOLLAR + ", T" + DOLLAR + "1" + DOLLAR + ", T" + DOLLAR + "2" + DOLLAR + ", T" + DOLLAR + "3" + DOLLAR),
    (re.compile(r'\bV0/V1/V2/V3\b'),           "T" + DOLLAR + "0" + DOLLAR + "/T" + DOLLAR + "1" + DOLLAR + "/T" + DOLLAR + "2" + DOLLAR + "/T" + DOLLAR + "3" + DOLLAR),
    (re.compile(r'\bV0/V1/V2\b'),              "T" + DOLLAR + "0" + DOLLAR + "/T" + DOLLAR + "1" + DOLLAR + "/T" + DOLLAR + "2" + DOLLAR),
    (re.compile(r'V3 wins \(sig\.\):'),        "T" + DOLLAR + "3" + DOLLAR + " wins (sig.):"),
    (re.compile(r' vs V0, '),                  " vs T" + DOLLAR + "0" + DOLLAR + ", "),
    (re.compile(r' vs V1, '),                  " vs T" + DOLLAR + "1" + DOLLAR + ", "),
    (re.compile(r' vs V2 '),                   " vs T" + DOLLAR + "2" + DOLLAR + " "),
    (re.compile(r'V0 (always-trigger)'),       "T" + DOLLAR + "0" + DOLLAR + " (always-trigger)"),
    (re.compile(r'V1 \(entropy-only\)'),       "T" + DOLLAR + "1" + DOLLAR + " (entropy-only)"),
    (re.compile(r'V2 \(entr\+stag\)'),         "T" + DOLLAR + "2" + DOLLAR + " (entr+stag)"),
    (re.compile(r'V3 \(triple\)'),             "T" + DOLLAR + "3" + DOLLAR + " (triple)"),
    (re.compile(r'V3 wins \(sig\. at'),        "T" + DOLLAR + "3" + DOLLAR + " wins (sig. at"),
    (re.compile(r'V3 < V\$x\$ means'),         "T" + DOLLAR + "3" + DOLLAR + " < T" + DOLLAR + "x" + DOLLAR + " means"),
    (re.compile(r'V3 < V'),                    "T" + DOLLAR + "3" + DOLLAR + " < T" + DOLLAR),
    # "V3 > V0" / "V3 > V1" / "V3 > V2" used in narrative
    (re.compile(r'V3 > V0'),                   "T" + DOLLAR + "3" + DOLLAR + " > T" + DOLLAR + "0" + DOLLAR),
    (re.compile(r'V3 > V1'),                   "T" + DOLLAR + "3" + DOLLAR + " > T" + DOLLAR + "1" + DOLLAR),
    (re.compile(r'V3 > V2'),                   "T" + DOLLAR + "3" + DOLLAR + " > T" + DOLLAR + "2" + DOLLAR),
    (re.compile(r'V1 < V3'),                   "T" + DOLLAR + "1" + DOLLAR + " < T" + DOLLAR + "3" + DOLLAR),
    # LaTeX-output lines:  "V3 vs V0 (always-trigger)" etc.
    (re.compile(r"V3 vs V0 \(always-trigger\)"), "T" + DOLLAR + "3" + DOLLAR + " vs T" + DOLLAR + "0" + DOLLAR + " (always-trigger)"),
    (re.compile(r"V3 vs V1 \(entropy\)"),        "T" + DOLLAR + "3" + DOLLAR + " vs T" + DOLLAR + "1" + DOLLAR + " (entropy)"),
    (re.compile(r"V3 vs V2 \(entr\+stag\)"),     "T" + DOLLAR + "3" + DOLLAR + " vs T" + DOLLAR + "2" + DOLLAR + " (entr+stag)"),
    (re.compile(r"V3 vs V0/V1/V2"),             "T" + DOLLAR + "3" + DOLLAR + " vs T" + DOLLAR + "0" + DOLLAR + "/T" + DOLLAR + "1" + DOLLAR + "/T" + DOLLAR + "2" + DOLLAR),
    (re.compile(r"V3 losses \(sig"),            "T" + DOLLAR + "3" + DOLLAR + " losses (sig"),
]


for path in FILES:
    with open(path, "r", encoding="utf-8") as f:
        s = f.read()
    orig = s
    n_total = 0
    for pat, repl in PATTERNS:
        s, n = pat.subn(repl, s)
        n_total += n
    if s != orig:
        with open(path, "w", encoding="utf-8") as f:
            f.write(s)
        print(f"[patched] {path}  ({n_total} replacements)")
    else:
        print(f"[no change] {path}")
