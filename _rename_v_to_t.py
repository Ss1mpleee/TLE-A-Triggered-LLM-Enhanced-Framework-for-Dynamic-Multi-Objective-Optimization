# -*- coding: utf-8 -*-
"""
Rename V$0$/V$1$/V$2$/V$3$ -> T$0$/T$1$/T$2$/T$3$ in main_submission.tex
from line 800 onward (this is the new Section 6.11 + later discussion
that uses the NEW definition: V0=always, V1=entropy, V2=entr+stag,
V3=triple-signal/proposed).

The OLD definition (5.5.2, line 618-639: V0=no-LLM, V1=DE-LM-static,
V2=TLE) stays untouched.

ALSO fix the Discussion 3 (line 965) bug where V2/V0 are written
backwards: the new sentence becomes "a simple time-decaying
heuristic (V1) outperforms the UCB bandit (V2) on DF5 ..." which
matches the OLD 5.5.2 definition.
"""
import re
import sys

PATH = r"D:\新论文\论文\_submission\main_submission.tex"

DOLLAR = chr(36)  # '$'

with open(PATH, "r", encoding="utf-8") as f:
    content = f.read()

lines = content.split("\n")
new_lines = list(lines)

# 1) For lines 800 .. end, replace V$0$/V$1$/V$2$/V$3$ with T$0$/T$1$/T$2$/T$3$
# (1-indexed in the editor, 0-indexed in Python)
RE_V_DOLLAR = re.compile(r"V\$([0-3])\$")
renamed_count = 0
for i in range(799, len(new_lines)):  # 0-indexed: line 800 = idx 799
    line = new_lines[i]
    new_line, n = RE_V_DOLLAR.subn(r"T" + DOLLAR + r"\1" + DOLLAR, line)
    if n > 0:
        renamed_count += n
        new_lines[i] = new_line

print(f"[rename] replaced {renamed_count} V$x$ -> T$x$ from line 800 onward")

# 2) Fix the line 965 Discussion 3 bug
# Original: "a simple time-decaying heuristic (V2) outperforms the UCB bandit (V0) on DF5"
# The OLD 5.5.2 says: V0=no-LLM, V1=DE-LM-static(heuristic decay), V2=TLE(UCB1 bandit)
# So: heuristic = V1, UCB bandit = V2.  Replace V2->V1, V0->V2 in that one sentence.
IDX_965 = 964  # 0-indexed
old_965 = new_lines[IDX_965]
print(f"\n[before line 965]\n{old_965}\n")

# Use literal substrings (not regex) to keep it surgical:
needle1 = "a simple time-decaying heuristic (V" + DOLLAR + "2" + DOLLAR + ") outperforms the UCB bandit (V" + DOLLAR + "0" + DOLLAR + ")"
fix1    = "a simple time-decaying heuristic (V" + DOLLAR + "1" + DOLLAR + ") outperforms the UCB bandit (V" + DOLLAR + "2" + DOLLAR + ")"
if needle1 in old_965:
    new_965 = old_965.replace(needle1, fix1)
    new_lines[IDX_965] = new_965
    print(f"[after line 965]\n{new_965}\n")
else:
    print("WARNING: Discussion 3 fix needle not found exactly.  Check the line.")
    sys.exit(1)

# Write back
new_content = "\n".join(new_lines)
with open(PATH, "w", encoding="utf-8") as f:
    f.write(new_content)

print("[done] main_submission.tex updated.")
