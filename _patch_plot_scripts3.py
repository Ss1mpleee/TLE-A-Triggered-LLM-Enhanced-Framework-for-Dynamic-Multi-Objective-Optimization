# -*- coding: utf-8 -*-
"""
Third pass: with the negative-lookbehind/lookahead trick, swap any
standalone V0/V1/V2/V3 word to T$0$/T$1$/T$2$/T$3$ in display strings
and comments.  KEY names (V0_baseline etc.) and variable names
(VERSIONS list) are NOT touched because the next char is '_' which
is a word char and breaks \b.
"""
import re

DOLLAR = chr(36)

FILES = [
    r"D:\新论文\实验\experiments\plot_ablation_lite.py",
    r"D:\新论文\实验\experiments\plot_outliers_and_invocations.py",
    r"D:\新论文\实验\experiments\stats_ablation_crossllm.py",
]

# Vx where x in {0,1,2,3} AND not followed by '_' (to avoid KEY names) AND not preceded by '_'
# i.e. the Vx is a standalone token.
STANDALONE_VX = re.compile(r"(?<![A-Za-z0-9_])V([0-3])(?![A-Za-z0-9_])")

def swap(m):
    return "T" + DOLLAR + m.group(1) + DOLLAR

for path in FILES:
    with open(path, "r", encoding="utf-8") as f:
        s = f.read()
    new_s, n = STANDALONE_VX.subn(swap, s)
    if n > 0:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_s)
        print(f"[patched3] {path}  ({n} standalone Vx replaced)")
    else:
        print(f"[no change3] {path}")
