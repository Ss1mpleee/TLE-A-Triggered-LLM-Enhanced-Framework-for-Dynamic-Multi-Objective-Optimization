PATH = r"D:\新论文\论文\_submission\cover_letter.tex"
with open(PATH, "r", encoding="utf-8") as f:
    raw = f.read()

# 1. "IGD \in [11242, 34606]" -> "IGD $\in [11242, 34606]$"
broken = "IGD \\in [11242, 34606] on DF2"
fixed  = "IGD $\\in [11242, 34606]$ on DF2"

if broken in raw:
    new_raw = raw.replace(broken, fixed)
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(new_raw)
    print("[cover-fix10] replaced")
else:
    print("[cover-fix10] not found")
