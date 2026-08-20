PATH = r"D:\新论文\论文\_submission\cover_letter.tex"
with open(PATH, "r", encoding="utf-8") as f:
    raw = f.read()

# "$\chi^2 = 1.135, p = 0.567$ (\mathrm{CD} = 0.886$ for $k = 3$, $N = 14$)" — \mathrm in text mode
broken = "$\\chi^2 = 1.135, p = 0.567$ (\\mathrm{CD} = 0.886$ for $k = 3$, $N = 14$)"
fixed  = "$\\chi^2 = 1.135, p = 0.567$ ($\\mathrm{CD} = 0.886$ for $k = 3$, $N = 14$)"

if broken in raw:
    new_raw = raw.replace(broken, fixed)
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(new_raw)
    print("[cover-fix9] replaced")
else:
    print("[cover-fix9] not found")
