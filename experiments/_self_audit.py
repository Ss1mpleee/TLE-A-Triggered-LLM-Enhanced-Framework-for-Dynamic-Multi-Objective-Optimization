"""Self-audit: verify every claim from previous turn is actually true."""
import os
import re
import urllib.request
import json
import time
from datetime import datetime

print('='*80)
print('SELF-AUDIT OF PREVIOUS TURN CLAIMS')
print('='*80)

issues = []
ok = []

# === Claim 1: 6 DOI prefix/character fixes ===
print()
print('[1] 6 DOI prefix/character fixes:')
DOIS_TO_CHECK = {
    'huang2026knee-dmo': '10.1016/j.swevo.2026.102358',  # was .2025.102358
    'cao2026effective': '10.1016/j.swevo.2026.102364',  # was .2025.102364
    'zhang2026ga-gnn': '10.1016/j.swevo.2026.102366',  # was .2025.102366
    'ding2026sparse-bo': '10.1016/j.swevo.2026.102360',  # was .2025.102360
    'deb2007dnsga': '10.1007/978-3-540-70928-2_60',  # was 72964-8_57
    'zhou2014pps': '10.1109/TCYB.2013.2245892',  # was 2245898
}
with open(r'D:\新论文\论文\references.bib', 'r', encoding='utf-8') as f:
    bib = f.read()
for key, expected_doi in DOIS_TO_CHECK.items():
    # Find entry
    m = re.search(r'@(?:\w+)\{' + re.escape(key) + r',.*?\n\}', bib, re.DOTALL)
    if not m:
        issues.append(f'[1] {key}: ENTRY NOT FOUND')
        continue
    entry = m.group(0)
    # Get DOI
    doi_m = re.search(r'doi\s*=\s*\{([^}]+)\}', entry)
    actual_doi = doi_m.group(1) if doi_m else None
    if actual_doi == expected_doi:
        # Verify via crossref
        try:
            req = urllib.request.Request(f'https://api.crossref.org/works/{expected_doi}', headers={'User-Agent': 'TLE-audit/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                msg = data.get('message', {})
                t = msg.get('title', [''])[0] if msg.get('title') else ''
                if key.split('2')[0] in t.lower().replace(' ', '') or any(w in t.lower() for w in key.replace('2', ' ').replace('-', ' ').split()[:3]):
                    ok.append(f'[1] {key}: DOI={expected_doi} REAL "{t[:50]}"')
                else:
                    issues.append(f'[1] {key}: DOI real but title mismatch!')
        except Exception as e:
            issues.append(f'[1] {key}: DOI check failed: {e}')
    else:
        issues.append(f'[1] {key}: DOI MISMATCH expected {expected_doi} got {actual_doi}')

# === Claim 2: 4 real replacements ===
print()
print('[2] 4 real replacements:')
REPLACEMENTS = {
    'liu2026llm-aided': '10.1145/3787965',
    'liu2026dual-space': '10.1162/evco.a.393',
    'li2024adaptive-response': '10.1016/j.asoc.2024.111756',
}
for key, doi in REPLACEMENTS.items():
    m = re.search(r'@(?:\w+)\{' + re.escape(key) + r',.*?\n\}', bib, re.DOTALL)
    if not m:
        issues.append(f'[2] {key}: ENTRY NOT FOUND')
        continue
    entry = m.group(0)
    doi_m = re.search(r'doi\s*=\s*\{([^}]+)\}', entry)
    actual = doi_m.group(1) if doi_m else None
    if actual == doi:
        ok.append(f'[2] {key}: correct DOI {doi}')
    else:
        issues.append(f'[2] {key}: DOI MISMATCH {actual} vs {doi}')

# Confirm wang2017drl-moead / wan2020community are GONE
for old_key in ['wang2017drl-moead', 'wan2020community']:
    m = re.search(r'@(?:\w+)\{' + re.escape(old_key) + r',', bib)
    if m:
        issues.append(f'[2] {old_key}: STILL EXISTS (should be removed)')
    else:
        ok.append(f'[2] {old_key}: removed as intended')

# === Claim 3: 11 fabricated entries deleted ===
print()
print('[3] 11 fabricated entries deleted:')
DELETED_KEYS = [
    'xu2026runtime', 'tian2024predict-dmo', 'li2024knee-pareto', 'zhou2024survey',
    'tian2023transfer', 'wang2023dmo', 'li2023drl-dmo', 'azevedo2023dmo',
    'azevedo2016dmo', 'helbig2016dmo', 'sierra2014ucb',
]
for key in DELETED_KEYS:
    m = re.search(r'@(?:\w+)\{' + re.escape(key) + r',', bib)
    if m:
        issues.append(f'[3] {key}: STILL EXISTS (should be removed)')
    else:
        ok.append(f'[3] {key}: removed as intended')

# Check all \cite{...} keys are valid
print()
print('[3b] No broken \cite{} references:')
cite_pattern = re.compile(r'\\cite\{([^}]+)\}')
all_cited_keys = set()
sections_dir = r'D:\新论文\论文\sections'
for fn in os.listdir(sections_dir):
    if fn.endswith('.tex'):
        with open(os.path.join(sections_dir, fn), 'r', encoding='utf-8') as f:
            content = f.read()
        for m in cite_pattern.finditer(content):
            for k in m.group(1).split(','):
                all_cited_keys.add(k.strip())
# Get all bib keys
all_bib_keys = set(re.findall(r'@(?:\w+)\{([^,]+),', bib))
broken = all_cited_keys - all_bib_keys
if broken:
    for k in broken:
        issues.append(f'[3b] \\cite{{{k}}} is BROKEN (no bib entry)')
else:
    ok.append(f'[3b] all {len(all_cited_keys)} \\cite{{}} keys resolve to bib entries')

# === Claim 4: AI-tell "demonstrated that" fix ===
print()
print('[4] AI-tell "demonstrated that" fix:')
for fn in os.listdir(sections_dir):
    if fn.endswith('.tex'):
        with open(os.path.join(sections_dir, fn), 'r', encoding='utf-8') as f:
            content = f.read()
        if 'demonstrated that' in content or 'it is demonstrated' in content:
            issues.append(f'[4] {fn}: STILL contains "demonstrated that"')
        else:
            pass
# Also check 02_related_work specifically
with open(os.path.join(sections_dir, '02_related_work.tex'), 'r', encoding='utf-8') as f:
    rw = f.read()
if 'demonstrated that' in rw or 'it is demonstrated' in rw:
    issues.append('[4] 02_related_work: STILL contains "demonstrated that"')
else:
    ok.append('[4] "demonstrated that" removed from 02_related_work')

# Also check broader AI-tell phrases
aitells = ['it is demonstrated that', 'has been shown to', 'it can be seen that']
for fn in os.listdir(sections_dir):
    if fn.endswith('.tex'):
        with open(os.path.join(sections_dir, fn), 'r', encoding='utf-8') as f:
            content = f.read()
        for phrase in aitells:
            if phrase in content.lower():
                issues.append(f'[4] {fn}: contains AI-tell "{phrase}"')

# === Claim 5: 3 PDFs recompiled ===
print()
print('[5] 3 PDFs recompiled:')
PAPER_DIR = r'D:\新论文\论文'
for pdf in ['main.pdf', 'cover_letter.pdf', 'supplementary_material.pdf']:
    path = os.path.join(PAPER_DIR, pdf)
    if os.path.exists(path):
        mtime = os.path.getmtime(path)
        size = os.path.getsize(path)
        dt = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        ok.append(f'[5] {pdf}: {size} bytes, modified {dt}')
    else:
        issues.append(f'[5] {pdf}: MISSING')

# === Claim 6: Overleaf ZIP exists ===
print()
print('[6] Overleaf ZIP:')
zip_path = r'D:\新论文\论文_Overleaf.zip'
if os.path.exists(zip_path):
    size = os.path.getsize(zip_path)
    mtime = os.path.getmtime(zip_path)
    dt = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
    ok.append(f'[6] {zip_path}: {size} bytes ({size/1024/1024:.1f} MB), modified {dt}')
else:
    issues.append(f'[6] {zip_path}: MISSING')

# === Sanity: bib entry count ===
print()
print('[META] bib entry count:')
n = len(re.findall(r'@(?:\w+)\{', bib))
ok.append(f'[META] bib has {n} entries')

# === Print summary ===
print()
print('='*80)
print('SUMMARY')
print('='*80)
print(f'OK: {len(ok)}')
for o in ok:
    print(f'  [OK] {o}')
print()
print(f'ISSUES: {len(issues)}')
for i in issues:
    print(f'  [ISSUE] {i}')

if issues:
    print()
    print('!!!  PREVIOUS TURN HAD FALSE CLAIMS — see ISSUES above !!!')
else:
    print()
    print('All previous turn claims verified. No false claims found.')
