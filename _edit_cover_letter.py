#!/usr/bin/env python3
"""T70 round 1: cover letter abbreviation additions and typo fix."""
import io
import sys
from pathlib import Path

f = Path(r'D:\新论文\论文\_submission\cover_letter.tex')
content = f.read_text(encoding='utf-8')

# 1) UCB1 definition
old1 = r"and with a \emph{UCB1 bandit budget scheduler} with a stationary"
new1 = r"and with a \emph{UCB1 (Upper Confidence Bound 1) bandit budget scheduler} with a stationary"
assert old1 in content, "UCB1 edit anchor not found"
content = content.replace(old1, new1, 1)

# 2) CEC definition
old2 = r"On the full CEC~2018 dynamic benchmark suite"
new2 = r"On the full CEC~2018 (Congress on Evolutionary Computation 2018) dynamic benchmark suite"
assert old2 in content, "CEC edit anchor not found"
content = content.replace(old2, new2, 1)

# 3) cost-normalized IGD: add IGD definition (inverted generational distance) on first use
old3 = r"TLE achieves a cost-normalized IGD of 18.88"
new3 = r"TLE achieves a cost-normalized IGD (inverted generational distance) of 18.88"
assert old3 in content, "IGD edit anchor not found"
content = content.replace(old3, new3, 1)

# 4) Nemenyi critical-difference expansion
old4 = r"within the Nemenyi CD bar of"
new4 = r"within the Nemenyi critical-difference bar of"
assert old4 in content, "Nemenyi edit anchor not found"
content = content.replace(old4, new4, 1)

# 5) DNSGA-II-A, PPS-DMOEA first-use full names
old5 = r"DE, PPS-DMOEA, and DE-LM-static-trigger"
new5 = r"DE, PPS-DMOEA (Population Prediction Strategy DMOEA), and DE-LM-static-trigger"
assert old5 in content, "PPS edit anchor not found"
content = content.replace(old5, new5, 1)

old6 = r"diversity-injection baseline DNSGA-II-A at fleet sizes"
new6 = r"diversity-injection baseline DNSGA-II-A (Dynamic NSGA-II with random immigrants) at fleet sizes"
assert old6 in content, "DNSGA-II-A edit anchor not found"
content = content.replace(old6, new6, 1)

# 6) "Multi-Unmanned-Aerial-Vehicle" full name already in cover; UAV expanded
old7 = r"multi-Unmanned-Aerial-Vehicle task-allocation scenario"
new7 = r"multi-Unmanned Aerial Vehicle (UAV) task-allocation scenario"
assert old7 in content, "UAV edit anchor not found"
content = content.replace(old7, new7, 1)

# 7) Fix the duplicated "to the best of the authors"
old8 = r"To the best of the authorsto the best of the authors' knowledge"
new8 = r"To the best of the authors' knowledge"
assert old8 in content, "Typo fix anchor not found"
content = content.replace(old8, new8, 1)

# 8) Add explicit "we" / "the authors" usage to passive where it's currently
#    "the present version addresses this concern" (no first-person to change,
#    but make sure no first-person present)

f.write_text(content, encoding='utf-8')
print("cover_letter.tex: 8 edits applied")
