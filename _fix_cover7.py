PATH = r"D:\新论文\论文\_submission\cover_letter.tex"
with open(PATH, "r", encoding="utf-8") as f:
    raw = f.read()

fixes = [
    # 1. `\\\\ 0.74) but TLE achieves a \\\\.37\\times\\\\$`
    ("\\\\ 0.74) but TLE achieves a \\\\.37\\times\\\\$",
     " 0.74) but TLE achieves a $\\mathbf{2.37\\times}$"),
    # 2. `\\\\ \\leq 0.0312\\\\$`
    ("\\\\ \\leq 0.0312\\\\$", "$\\mathbf{p} \\leq 0.0312$"),
    # 3. `\\\\ = 30\\\\$ seeds per model per problem, \\\\ \\times 14 \\times 30 = 1260\\\\$`
    ("\\\\ = 30\\\\$ seeds per model per problem, \\\\ \\times 14 \\times 30 = 1260\\\\$",
     "$n = 30$ seeds per model per problem, $3 \\times 14 \\times 30 = 1260$"),
    # 4. `\\\\' knowledge, no prior` -- first apostrophe eaten
    ("\\\\' knowledge, no prior LLM-EC or DMO work has combined",
     "to the best of the authors' knowledge, no prior LLM-EC or DMO work has combined"),
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
    print(f"[cover-fix7] {n} patterns fixed")
else:
    print("[cover-fix7] no change")
