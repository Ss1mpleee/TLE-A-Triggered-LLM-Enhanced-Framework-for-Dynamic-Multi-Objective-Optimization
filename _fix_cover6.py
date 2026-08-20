PATH = r"D:\新论文\论文\_submission\cover_letter.tex"
with open(PATH, "r", encoding="utf-8") as f:
    raw = f.read()

# File has 'chi\textasciicircum{}2 = 1.135, p = 0.567'
# In Python string: "chi\\textasciicircum{}2 = 1.135, p = 0.567"
broken = "chi\\textasciicircum{}2 = 1.135, p = 0.567"
fixed  = "$\\chi^2 = 1.135, p = 0.567$"

if broken in raw:
    new_raw = raw.replace(broken, fixed)
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(new_raw)
    print(f"[cover-fix6] replaced")
else:
    print(f"[cover-fix6] not found")
