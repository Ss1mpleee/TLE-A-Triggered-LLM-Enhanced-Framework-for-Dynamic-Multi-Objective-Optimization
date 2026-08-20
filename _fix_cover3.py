# -*- coding: utf-8 -*-
"""
Direct character-level replacement for the remaining cover_letter
damage.  After this, the file should be clean.
"""
PATH = r"D:\新论文\论文\_submission\cover_letter.tex"
with open(PATH, "r", encoding="utf-8") as f:
    raw = f.read()

# Broken patterns observed:
# 1. "\\mathrm{CD} = 1.254$ for\\ = 4\\$, \\ = 14\\$)"  (cd=1.254)
# 2. "chi\\textasciicircum{}2 = 1.135, p = 0.567 (\\mathrm{CD} = 0.886 for \\ = 3\\$, \\ = 14\\$)"  (cd=0.886)
# 3. "Wilcoxon \\ = 0.008\\$, Cohen\\'s \\ = -0.79\\$)"
# 4. "IGD \\$= 0.0\\$ on all 30 seeds"

# Use direct string replacement; raw characters in the file are
# exactly: \ \mathrm{CD} = 1.254$ for\ \ = 4\ \$, \ \ = 14\ \$
# In a Python string literal we write each \ as \\
# So the broken sequence is:
broken1 = "\\mathrm{CD} = 1.254$ for\\ = 4\\$, \\ = 14\\$)"
fixed1  = "$\\mathrm{CD} = 1.254$ for $k = 4$, $N = 14$)"

# Broken: chi\textasciicircum{}2 = 1.135, p = 0.567 (\mathrm{CD} = 0.886 for \ = 3\$, \ = 14\$)
broken2 = "chi\\textasciicircum{}2 = 1.135, p = 0.567 (\\mathrm{CD} = 0.886 for \\ = 3\\$, \\ = 14\\$)"
fixed2  = "$\\chi^2 = 1.135, p = 0.567$ ($\\mathrm{CD} = 0.886$ for $k = 3$, $N = 14$)"

# Broken: Wilcoxon \ = 0.008\$, Cohen\'s \ = -0.79\$)
broken3 = "Wilcoxon \\ = 0.008\\$, Cohen\\'s \\ = -0.79\\$)"
fixed3  = "Wilcoxon $p = 0.008$, Cohen's $d = -0.79$)"

# Broken: IGD \$= 0.0\$ on all 30 seeds
broken4 = "IGD \\$= 0.0\\$ on all 30 seeds"
fixed4  = "IGD $= 0.0$ on all 30 seeds"

fixes = [
    (broken1, fixed1),
    (broken2, fixed2),
    (broken3, fixed3),
    (broken4, fixed4),
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
    print(f"[cover-fix3] {n} patterns fixed")
else:
    print("[cover-fix3] no change")
