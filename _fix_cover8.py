PATH = r"D:\新论文\论文\_submission\cover_letter.tex"
with open(PATH, "r", encoding="utf-8") as f:
    raw = f.read()

fixes = [
    # 1. "Friedman \$\chi^2 = 1.135, p = 0.567"  (extra \ before $)
    ("Friedman \\$\\chi^2 = 1.135, p = 0.567", "Friedman $\\chi^2 = 1.135, p = 0.567"),
    # 2. "TLE reduces task cost by \mathbf{21.2\%}/..."  (\mathbf in text mode)
    ("TLE reduces task cost by \\mathbf{21.2\\%}/\\mathbf{20.4\\%}/\\mathbf{19.0\\%}",
     "TLE reduces task cost by $\\mathbf{21.2\\%}/\\mathbf{20.4\\%}/\\mathbf{19.0\\%}$"),
    # 3. "the matching \mathbf{2.37\times}"  (extra text-mode \mathbf)
    # Actually this is in "(0.73 vs. 0.74) but TLE achieves a $\mathbf{2.37\times}$"  - should be fine
    # Let me check by re-running
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
    print(f"[cover-fix8] {n} patterns fixed")
