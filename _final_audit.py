#!/usr/bin/env python3
import sys, re, hashlib, zipfile
sys.stdout.reconfigure(encoding='utf-8')

print('=' * 70)
print('FINAL VERIFICATION SUMMARY')
print('=' * 70)

with open(r'D:\新论文\论文\_submission\main_submission.tex', 'r', encoding='utf-8') as f:
    main = f.read()

print()
print('--- T70 round 1 (4-dimension review) ---')
we = len(re.findall(r'\bwe\b', main, re.I))
our = len(re.findall(r'\bour\b', main, re.I))
us = len(re.findall(r'\bus\b', main, re.I))
print(f'  First-person pronouns: we={we}, our={our}, us={us}')
ai_tells = ['orchestrate', 'To summarize', 'delve into', 'leverage', 'harness',
            'facilitate', 'elucidate', 'paradigm shift']
for t in ai_tells:
    present = t.lower() in main.lower()
    print(f'  AI-tell "{t}": {"STILL PRESENT" if present else "removed"}')

print()
print('--- T70 round 2 (abbreviation first-use) ---')
for abbr, full in [
    ('LLM-EC', 'large-language-model evolutionary computation'),
    ('DNSGA-II-A', 'Dynamic Non-dominated Sorting'),
    ('PPS-DMOEA', 'Prediction-based Dynamic Multi-Objective'),
    ('MOEA/DD', 'Multi-Objective Evolutionary Algorithm based on Dominance'),
    ('JSON', 'JavaScript object notation'),
    ('CEC', 'Congress on Evolutionary Computation'),
    ('UAV', 'Unmanned Aerial Vehicle'),
    ('IGD', 'inverted generational distance'),
    ('UCB1', 'Upper Confidence Bound 1'),
    ('NSGA-II', 'Non-dominated Sorting Genetic Algorithm II'),
]:
    has = bool(re.search(re.escape(full), main, re.I))
    print(f'  {abbr:12s}: {"OK" if has else "MISSING"}')

print()
print('--- T70 round 3 (new/novel replacement) ---')
patterns = [
    ('two previously unobserved failure modes (L179)', r'surfaces two previously unobserved failure modes'),
    ('two previously unobserved failure modes emerge (L747)', r'two previously unobserved failure modes emerge'),
    ('expanded data set (L249)', r'expanded data set'),
    ('two extended large-scale ablations (L249)', r'two extended large-scale ablations are added'),
    ('extended trigger-ablation (L989)', r'For the extended trigger-ablation'),
    ('extended trigger-ablation (L992)', r'The extended trigger-ablation'),
    ('LLM-coordinated (L1019)', r'LLM-coordinated evolutionary search'),
]
for label, pat in patterns:
    has = bool(re.search(pat, main))
    print(f'  {label}: {"OK" if has else "MISSING"}')

print()
print('--- Cost-qual numbers ---')
n_2_34 = len(re.findall(r'2\.34\\times', main))
n_18_88 = len(re.findall(r'18\.88', main))
n_44_18 = len(re.findall(r'44\.18', main))
n_17226 = len(re.findall(r'17[,]?226', main))
n_2520 = len(re.findall(r'2[,]?520', main))
n_n30 = len(re.findall(r'n = 30', main))
print(f'  2.34×: {n_2_34}x')
print(f'  18.88: {n_18_88}x')
print(f'  44.18: {n_44_18}x')
print(f'  17,226 cache: {n_17226}x')
print(f'  2,520-run: {n_2520}x')
print(f'  n=30: {n_n30}x')

print()
print('--- Section sync ---')
import os
for sec in ['01_introduction', '02_related_work', '03_method', '03_theory',
            '04_experimental_setup', '05_results', '06_discussion',
            '07_conclusion', 'A_appendix']:
    path = f'D:\\新论文\\论文\\sections\\{sec}.tex'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f'  {sec}.tex: {len(content):,} chars')
    else:
        print(f'  {sec}.tex: MISSING')

print()
print('--- Zip integrity ---')
for zip_name in ['TLE_SWEVO_Overleaf.zip', 'TLE_SWEVO_PDFs_only.zip']:
    zip_path = f'D:\\新论文\\{zip_name}'
    if os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zf:
            n = len(zf.namelist())
            bad = zf.testzip()
            size = os.path.getsize(zip_path)
            print(f'  {zip_name}: {n} files, {size:,} bytes, integrity: {"OK" if bad is None else bad}')
    else:
        print(f'  {zip_name}: MISSING')

print()
print('--- _TO_DELETE/ false-positive check ---')
# Compare 2 flagged items
def hash_file(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]

for name in ['fig_budget_comparison.pdf', 'highlights.txt']:
    in_sub = hash_file(f'D:\\新论文\\论文\\_submission\\{name}')
    in_del = hash_file(f'D:\\新论文\\论文\\_TO_DELETE\\{name}')
    same = in_sub == in_del
    print(f'  {name}: _submission={in_sub}, _TO_DELETE={in_del} -> {"IDENTICAL" if same else "different"}')
    if same:
        print(f'    (timestamp diff was just file system touch, not real change)')
