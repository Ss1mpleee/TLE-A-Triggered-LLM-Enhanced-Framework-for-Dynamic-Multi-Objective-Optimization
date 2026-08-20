#!/usr/bin/env python3
"""T70 final pre-submission audit."""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

main = open(r'D:\新论文\论文\_submission\main_submission.tex', 'r', encoding='utf-8').read()
bib = open(r'D:\新论文\论文\_submission\references.bib', 'r', encoding='utf-8').read()
supp = open(r'D:\新论文\论文\_submission\supplementary_material.tex', 'r', encoding='utf-8').read()
cover = open(r'D:\新论文\论文\_submission\cover_letter.tex', 'r', encoding='utf-8').read()

print("=" * 70)
print("PRE-SUBMISSION FINAL AUDIT")
print("=" * 70)

# 1. Key numbers
print("\n--- 1. Key numbers in main ---")
checks = [
    ('2.34× cost-qual (abstract)', r'2\\.34\\times'),
    ('18.88 in abstract', r'18\.88'),
    ('44.18 in abstract', r'44\.18'),
    ('n = 30 in main', r'n = 30'),
    ('DF1--DF14 in main', r'DF1--DF14'),
    ('17,226 cache', r'17,?226'),
    ('2,520-run', r'2,?520'),
    ('21.2% UAV', r'21\.2\\%'),
    ('Wilcoxon p ≤ 0.0312', r'0\.0312'),
    ('CEC 2018', r'CEC.*2018'),
    ('UCB1 full name', r'Upper Confidence Bound 1'),
    ('IGD full name', r'[Ii]nverted [Gg]enerational [Dd]istance'),
    ('NSGA-II full name', r'Non-dominated Sorting Genetic Algorithm II'),
    ('DNSGA-II-A full name', r'Dynamic Non-dominated Sorting'),
    ('MOEA/DD full name', r'Multi-Objective Evolutionary Algorithm based on Dominance'),
    ('PPS-DMOEA full name', r'Prediction-based Dynamic'),
    ('UAV full name', r'Unmanned Aerial Vehicle'),
    ('JSON full name', r'JavaScript object notation'),
]
ok = 0
for label, pat in checks:
    if re.search(pat, main):
        print(f"  ✓ {label}")
        ok += 1
    else:
        print(f"  ✗ MISSING: {label}")
print(f"  {ok}/{len(checks)} key checks passed")

# 2. First-person
print("\n--- 2. First-person pronouns ---")
for label, txt in [('main', main), ('supp', supp), ('cover', cover)]:
    we = len(re.findall(r'\bwe\b', txt))
    our = len(re.findall(r'\bour\b', txt))
    us = len(re.findall(r'\bus\b', txt))
    print(f"  {label}: we={we}, our={our}, us={us}")

# 3. AI tells
print("\n--- 3. AI-tell phrases ---")
ai = ['delve into', 'leverage', 'harness', 'facilitate', 'elucidate',
      'paradigm shift', 'To summarize', 'It is worth noting', 'navigate the complexities']
ai_total = 0
for label, txt in [('main', main), ('supp', supp), ('cover', cover)]:
    for p in ai:
        n = len(re.findall(re.escape(p), txt, re.I))
        if n > 0:
            print(f"  {label}: {n}x '{p}'")
            ai_total += n
if ai_total == 0:
    print(f"  ✓ no AI-tell phrases")

# 4. new/novel promotional use
print("\n--- 4. new/novel promotional use ---")
patterns = [
    r'new framework', r'novel framework', r'novel approach', r'novel method',
    r'novel algorithm', r'new algorithm', r'novel technique', r'new technique',
    r'novel design', r'novel view',
]
new_total = 0
for label, txt in [('main', main), ('supp', supp), ('cover', cover)]:
    for p in patterns:
        n = len(re.findall(p, txt, re.I))
        if n > 0:
            print(f"  {label}: {n}x '{p}'")
            new_total += n
if new_total == 0:
    print(f"  ✓ no promotional new/novel in main/sup/cover")

# 5. References
print("\n--- 5. References ---")
n_entries = len(re.findall(r'^@', bib, re.M))
print(f"  Total entries: {n_entries}")
# Find all unique keys
keys = re.findall(r'@\w+\{([^,]+),', bib)
keys = set(keys)
print(f"  Unique keys: {len(keys)}")
# Check for duplicate keys
all_keys = re.findall(r'@\w+\{([^,]+),', bib)
from collections import Counter
c = Counter(all_keys)
dups = {k: v for k, v in c.items() if v > 1}
if dups:
    print(f"  ⚠ DUPLICATE KEYS: {dups}")
else:
    print(f"  ✓ no duplicate keys")

# 6. Undefined refs check
print("\n--- 6. Cross-reference integrity ---")
# Find all \cite{...} keys in main
cited = set()
for m in re.finditer(r'\\cite\{([^}]+)\}', main):
    keys_in = m.group(1).split(',')
    for k in keys_in:
        cited.add(k.strip())
print(f"  Cited keys in main: {len(cited)}")
# Check which cited keys are missing in bib
missing = cited - keys
if missing:
    print(f"  ⚠ MISSING in bib: {sorted(missing)}")
else:
    print(f"  ✓ all cited keys present in bib")
# Check which bib keys are not cited in main
unused = keys - cited
if unused:
    print(f"  ⚠ UNUSED in main: {sorted(unused)}")
else:
    print(f"  ✓ all bib keys cited in main")

# Same for supp
cited_supp = set()
for m in re.finditer(r'\\cite\{([^}]+)\}', supp):
    for k in m.group(1).split(','):
        cited_supp.add(k.strip())
missing_supp = cited_supp - keys
if missing_supp:
    print(f"  supp missing in bib: {sorted(missing_supp)}")

# Same for cover
cited_cover = set()
for m in re.finditer(r'\\cite\{([^}]+)\}', cover):
    for k in m.group(1).split(','):
        cited_cover.add(k.strip())
missing_cover = cited_cover - keys
if missing_cover:
    print(f"  cover missing in bib: {sorted(missing_cover)}")
else:
    print(f"  ✓ cover OK")

# 7. Cost-qual numbers cross-check
print("\n--- 7. Cost-qual internal consistency ---")
# In abstract: 2.34× should = 44.18/18.88
val_2_34 = 44.18 / 18.88
print(f"  44.18/18.88 = {val_2_34:.3f}  (should be 2.34×)")
# V_1 vs V_2 median IGD
v0 = 0.6804
v1 = 0.7333
v2 = 0.7283
print(f"  V0 (no LLM) median IGD: {v0}")
print(f"  V1 (heuristic) median IGD: {v1}")
print(f"  V2 (TLE) median IGD: {v2}")
# IGD/1000 calls
ig_v0 = 680.4
ig_v1 = 0.7333 * 1000 / 16.6
ig_v2 = 0.7283 * 1000 / 38.6
print(f"  V0 IGD/1000: {ig_v0:.2f}")
print(f"  V1 IGD/1000: {ig_v1:.2f}  (should be 44.18)")
print(f"  V2 IGD/1000: {ig_v2:.2f}  (should be 18.88)")

# 8. n=30 consistency
print("\n--- 8. n=30 consistency ---")
# Check the 6 algos × 14 problems × 30 seeds = 2520
n30_in = main.count('n = 30') + main.count('n=30') + main.count('$n=30$') + main.count('$n = 30$')
n5_in = main.count('n = 5') + main.count('n=5')
n8_in = main.count('n = 8') + main.count('n=8')
print(f"  n=30 mentions: {n30_in}")
print(f"  n=5 mentions: {n5_in}  (should be only for 16/32-UAV)")
print(f"  n=8 mentions: {n8_in}  (should be 0 -- stale)")

# 9. Check stale data
print("\n--- 9. Stale data check ---")
stale = ['5,156', '215-run', '11242', 'n=8', 'eight seeds', 'B_max = 60', 'RTX 5070']
stale_found = 0
for label, txt in [('main', main), ('supp', supp), ('cover', cover)]:
    for p in stale:
        if p in txt:
            print(f"  {label}: still has '{p}'")
            stale_found += 1
if stale_found == 0:
    print(f"  ✓ no stale data")

# 10. Date check
print("\n--- 10. PDF dates ---")
import os, datetime
for p in [r'D:\新论文\论文\_submission\main_submission.pdf',
          r'D:\新论文\论文\_submission\supplementary_material.pdf',
          r'D:\新论文\论文\_submission\cover_letter.pdf']:
    if os.path.exists(p):
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(p))
        age_h = (datetime.datetime.now() - mtime).total_seconds() / 3600
        print(f"  {os.path.basename(p)}: {mtime:%Y-%m-%d %H:%M:%S} ({age_h:.1f}h ago)")

# 11. Pages
print("\n--- 11. Page counts ---")
import subprocess
import os
for p in ['main_submission.pdf', 'supplementary_material.pdf', 'cover_letter.pdf']:
    full = os.path.join(r'D:\新论文\论文\_submission', p)
    cmd_script = f"""
import sys
try:
    from PyPDF2 import PdfReader
    r = PdfReader(r"{full}")
    print(f"  {p}: " + str(len(r.pages)) + " pages")
except Exception as e:
    print(f"  {p}: error " + str(e))
"""
    result = subprocess.run(['python', '-c', cmd_script], capture_output=True, text=True, encoding='utf-8')
    print(result.stdout.strip())
