# -*- coding: utf-8 -*-
import re
DOLLAR = chr(36)
PATH = r"D:\新论文\论文\_submission\supplementary_material.tex"
with open(PATH, "r", encoding="utf-8") as f:
    raw = f.read()
PATTERN = re.compile(r"V\$([0-3])\$")
REPL = r"T\$" + chr(36) + r"\1" + chr(36)
new_raw, n = PATTERN.subn(REPL, raw)
if new_raw != raw:
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(new_raw)
    print(f"[supp-fix] {n} V$x$ -> T$x$ replaced")
else:
    print("[supp-fix] no change")
