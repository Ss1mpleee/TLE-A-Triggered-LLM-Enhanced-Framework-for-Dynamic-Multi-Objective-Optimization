# -*- coding: utf-8 -*-
"""
Last-mile V$x$ -> T$x$ fix.  Use raw-string regex with literal \$ so
the dollar is treated as a literal character (otherwise $ in regex
means end-of-line / end-of-string).
"""
import re

DOLLAR = chr(36)  # '$'
PATH = r"D:\新论文\论文\_submission\main_submission.tex"

with open(PATH, "r", encoding="utf-8") as f:
    raw = f.read()

# Use raw-string pattern: r"V\$([0-3])\$"  so \$ is a literal $ match.
# Match any V$x$ in the file (not just standalone; safe because the only
# legitimate V$1$ etc. in this paper is the 5.5.2 V$0$/V$1$/V$2$ which
# we want to PRESERVE — so we restrict to lines 800 onwards).
PATTERN = re.compile(r"V\$([0-3])\$")
REPL = r"T" + DOLLAR + r"\1" + DOLLAR

lines = raw.split("\n")
new_lines = list(lines)

# Pass 1: rename lines 800..end (the 6.11 section + later discussions)
# Pass 2: also rename line 249 (Response to prior version paragraph)
TARGET_LINES = set(range(799, len(new_lines))) | {248}
n = 0
for i in sorted(TARGET_LINES):
    if i >= len(new_lines):
        continue
    line = new_lines[i]
    new_line, k = PATTERN.subn(REPL, line)
    if k > 0:
        new_lines[i] = new_line
        n += k

new_raw = "\n".join(new_lines)
if new_raw != raw:
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(new_raw)
    print(f"[final-fix2] {n} V$x$ -> T$x$ replaced")
else:
    print("[final-fix2] no change")
