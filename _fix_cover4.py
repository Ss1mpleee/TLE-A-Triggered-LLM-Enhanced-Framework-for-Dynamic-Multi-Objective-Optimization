# -*- coding: utf-8 -*-
"""
Final cover_letter cleanup.  The damage in the file uses LaTeX-style
`\\` (2 backslashes for forced line break).  In a Python string
literal that's 4 backslashes (`\\\\`).

In each broken sequence, the pattern is:
   for<BACKSLASH-BACKSLASH> = 4<BACKSLASH-BACKSLASH>$, <BACKSLASH-BACKSLASH> = 14<BACKSLASH-BACKSLASH>$
which should be:
   for $k = 4$, $N = 14$
"""
PATH = r"D:\新论文\论文\_submission\cover_letter.tex"
with open(PATH, "r", encoding="utf-8") as f:
    raw = f.read()

# 1.254$ for\\ = 4\\$, \\ = 14\\$)
broken1 = "1.254$ for" + "\\\\" + " = 4" + "\\\\" + "$, " + "\\\\" + " = 14" + "\\\\" + "$)"
fixed1  = "1.254$ for $k = 4$, $N = 14$)"

# 0.886 for\\ = 3\\$, \\ = 14\\$)
broken2 = "0.886 for " + "\\\\" + " = 3" + "\\\\" + "$, " + "\\\\" + " = 14" + "\\\\" + "$)"
fixed2  = "0.886$ for $k = 3$, $N = 14$)"

# Wilcoxon \\ = 0.008\\$, Cohen\'s \\ = -0.79\\$)
broken3 = "Wilcoxon " + "\\\\" + " = 0.008" + "\\\\" + "$, Cohen" + "\\\\" + "'s " + "\\\\" + " = -0.79" + "\\\\" + "$)"
fixed3  = "Wilcoxon $p = 0.008$, Cohen's $d = -0.79$)"

# IGD \\$= 0.0\\$ on all 30 seeds
broken4 = "IGD " + "\\\\" + "$= 0.0" + "\\\\" + "$ on all 30 seeds"
fixed4  = "IGD $= 0.0$ on all 30 seeds"

# Need to also fix the broken math `chi\textasciicircum{}2 = 1.135, p = 0.567`
# which is at the start of broken2
broken5 = "chi" + "\\\\" + "textasciicircum{}2 = 1.135, p = 0.567 ("
fixed5  = "$\\chi^2 = 1.135, p = 0.567$ ("

fixes = [
    (broken1, fixed1),
    (broken2, fixed2),
    (broken3, fixed3),
    (broken4, fixed4),
    (broken5, fixed5),
]

n = 0
new_raw = raw
for b, f in fixes:
    if b in new_raw:
        new_raw = new_raw.replace(b, f)
        n += 1
        print(f"[ok] {f[:60]}")
    else:
        print(f"[skip] {b[:60]}")

if new_raw != raw:
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(new_raw)
    print(f"[cover-fix4] {n} patterns fixed")
else:
    print("[cover-fix4] no change")
