# -*- coding: utf-8 -*-
import re

PATH = r"D:\新论文\论文\_submission\cover_letter.tex"
with open(PATH, "r", encoding="utf-8") as f:
    raw = f.read()

# Find broken patterns and replace them.  Working string-by-string:
fixes = [
    # (broken, fixed)
    # 1. (\\mathrm{CD} = 1.254 for\\ = 4\\$, \\ = 14\\$)
    (r"($\mathrm{CD} = 1.254$ for" + chr(92) + r" = 4" + chr(92) + r"$, " + chr(92) + r" = 14" + chr(92) + r"$)",
     "($\\mathrm{CD} = 1.254$ for $k = 4$, $N = 14$)"),
    # 2. chi\textasciicircum{}2 = 1.135, p = 0.567 (\mathrm{CD} = 0.886 for \ = 3\$, \ = 14\$)
    (r"chi\textasciicircum{}2 = 1.135, p = 0.567 (\mathrm{CD} = 0.886 for" + chr(92) + r" = 3" + chr(92) + r"$, " + chr(92) + r" = 14" + chr(92) + r"$)",
     "$\\chi^2 = 1.135, p = 0.567$ ($\\mathrm{CD} = 0.886$ for $k = 3$, $N = 14$)"),
    # 3. (i)~~V\$ (always-trigger)
    (r"(i)~~V\$ (always-trigger)",
     "(i)~~T$0$ (always-trigger)"),
    # 4. Wilcoxon \\ = 0.008\\$, Cohen\\'s \\ = -0.79\\$)
    (r"Wilcoxon " + chr(92) + r" = 0.008" + chr(92) + r"$, Cohen" + chr(92) + r"'s " + chr(92) + r" = -0.79" + chr(92) + r"$)",
     "Wilcoxon $p = 0.008$, Cohen's $d = -0.79$)"),
    # 5. IGD \\$= 0.0\\$ on all 30 seeds
    (r"IGD " + chr(92) + r"$= 0.0" + chr(92) + r"$ on all 30 seeds",
     "IGD $= 0.0$ on all 30 seeds"),
]

new_raw = raw
total = 0
for broken, fixed in fixes:
    if broken in new_raw:
        new_raw = new_raw.replace(broken, fixed)
        total += 1
        print(f"[ok] replaced: {fixed[:60]}...")
    else:
        print(f"[skip] not found: {broken[:60]}...")

if new_raw != raw:
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(new_raw)
    print(f"[cover-fix2] {total} patterns fixed")
else:
    print("[cover-fix2] no change")
